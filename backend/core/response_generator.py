"""
[Step 7] 응답 생성
시스템 프롬프트 + 의도별 프롬프트 + 검색 결과 + KG 컨텍스트를 조합하여
최종 응답을 생성합니다.

응답 끝에 [PROFILE_UPDATE] 블록이 있으면 파싱하여 profile_updates로 반환합니다.
"""
import json
from typing import Optional
from config import Intent, Weight
from models import UserProfile, RetrievedDocument, ChatSession
from prompts.templates import (
    SYSTEM_BASE,
    PROMPT_MEDICAL,
    PROMPT_EMOTION,
    PROMPT_POLICY,
    PROMPT_OUT_OF_SCOPE,
    RESPONSE_GENERATION,
    RESPONSE_GENERATION_EMOTION,
    RESPONSE_GENERATION_LIGHT,
)
from prompts import get_templates
from core.llm_client import LLMClient


# 의도 → 프롬프트 매핑
INTENT_PROMPTS = {
    Intent.MEDICAL: PROMPT_MEDICAL,
    Intent.EMOTION: PROMPT_EMOTION,
    Intent.POLICY: PROMPT_POLICY,
    Intent.OUT_OF_SCOPE: PROMPT_OUT_OF_SCOPE,
}


class ResponseGenerator:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        from core.profile_updater import ProfileUpdater
        self.profile_updater = ProfileUpdater(llm)

    def generate(
        self,
        user_input: str,
        intent: Intent,
        profile: UserProfile,
        reranked_docs: list[RetrievedDocument],
        kg_context: str,
        session: ChatSession,
        info_gap_hint: Optional[str] = None,
        weight: Optional[Weight] = None,
    ) -> str:
        """
        최종 응답을 생성합니다.

        1. 시스템 프롬프트 조립 (기본 + 의도별)
        2. 검색 결과를 컨텍스트로 변환
        3. 대화 히스토리 포함
        4. LLM 호출
        """
        # ── 1. 시스템 프롬프트 조립 ──
        system_prompt = self._build_system_prompt(intent, profile)

        # ── 2. 유저 메시지 조립 (검색 결과 + KG + 히스토리 포함) ──
        user_message = self._build_user_message(
            user_input=user_input,
            intent=intent,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint,
            profile=profile,
            weight=weight,
        )

        # ── 3. 대화 히스토리 (Responses API에 proper role로 전달) ──
        history = session.get_recent_history(n=4)
        # 현재 턴은 아직 세션에 저장 안 됐으므로 전체 전달
        prior_history = history if history else []

        # ── 4. LLM 호출 (답변 생성만, PROFILE_UPDATE 없이) ──
        raw_response = self.llm.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            history=prior_history if prior_history else None,
        )

        # 혹시 4o가 [PROFILE_UPDATE]를 출력했으면 제거
        response_text = raw_response.split("[PROFILE_UPDATE]")[0].strip()

        # ── 5. ProfileUpdater (mini 모델)로 프로필 업데이트 추출 ──
        profile_updates = self.profile_updater.extract(user_input, response_text, profile)

        return response_text, profile_updates

    def _parse_profile_update(self, raw_response: str) -> tuple:
        """(레거시) 응답에서 [PROFILE_UPDATE] 블록을 분리하여 (응답 텍스트, 업데이트 dict) 반환"""
        marker = "[PROFILE_UPDATE]"
        if marker not in raw_response:
            return raw_response.strip(), {}

        parts = raw_response.split(marker, 1)
        response_text = parts[0].strip()
        update_json = parts[1].strip()

        try:
            # ```json ... ``` 래핑 제거
            if update_json.startswith("```"):
                update_json = update_json.split("```")[1]
                if update_json.startswith("json"):
                    update_json = update_json[4:]
                update_json = update_json.strip()

            parsed = json.loads(update_json)
            if not isinstance(parsed, dict):
                return response_text, {}

            result = {}
            if parsed.get("fields"):
                result["fields"] = parsed["fields"]
            if parsed.get("notes"):
                result["notes"] = parsed["notes"]

            if result:
                print(f"  [ResponseGenerator] 프로필 업데이트 감지: {result}")

            return response_text, result

        except (json.JSONDecodeError, IndexError):
            return response_text, {}

    def _build_system_prompt(self, intent: Intent, profile: UserProfile) -> str:
        """기본 시스템 프롬프트 + 의도별 지침을 조합. mode에 따라 프롬프트 모듈 선택."""
        mode = getattr(profile, 'mode', None) or 'medical'
        t = get_templates(mode)

        nickname = getattr(profile, 'name', '') or '회원'
        base = t.SYSTEM_BASE.format(user_context=profile.context_summary())
        base = base.replace('{nickname}', nickname)

        mode_intent_prompts = {
            Intent.MEDICAL: t.PROMPT_MEDICAL,
            Intent.EMOTION: t.PROMPT_EMOTION,
            Intent.POLICY: t.PROMPT_POLICY,
            Intent.OUT_OF_SCOPE: t.PROMPT_OUT_OF_SCOPE,
        }
        intent_prompt = mode_intent_prompts.get(intent, "")
        if intent_prompt:
            intent_instructions = intent_prompt.split("### 참조 자료")[0]
            return base + "\n\n" + intent_instructions

        return base

    def _build_user_message(
        self,
        user_input: str,
        intent: Intent,
        reranked_docs: list[RetrievedDocument],
        kg_context: str,
        session: ChatSession,
        info_gap_hint: Optional[str] = None,
        weight: Optional[Weight] = None,
        profile: Optional[UserProfile] = None,
    ) -> str:
        """검색 결과, KG 컨텍스트를 포함한 유저 메시지 조립
        (대화 히스토리는 LLM history 파라미터로 별도 전달되므로 여기서는 포함하지 않음)"""
        mode = getattr(profile, 'mode', None) or 'medical' if profile else 'medical'
        t = get_templates(mode)

        # 정보 갭 힌트 블록
        info_gap_block = ""
        if info_gap_hint:
            info_gap_block = (
                f"\n\n### 추가 정보 수집 요청\n"
                f"사용자 프로필에 빠진 정보가 있습니다. "
                f"아래 질문을 대화 흐름상 자연스러울 때만 물어보세요.\n"
                f"⚠️ 주의: 지금 사용자가 다른 주제(증상, 감정, 시술 경험 등)에 집중하고 있다면 묻지 마세요. "
                f"억지로 답변 끝에 붙이지 말고, 대화 맥락상 연결이 자연스러울 때만 포함하세요.\n"
                f"질문: {info_gap_hint}"
            )

        # light 경로: RESPONSE_GENERATION_LIGHT 사용 (RAG 스킵)
        if weight == Weight.LIGHT:
            return t.RESPONSE_GENERATION_LIGHT.format(
                inmemory_context=kg_context or "(추가 정보 없음)",
                user_input=user_input,
            ) + info_gap_block

        # heavy 경로: 검색 결과를 텍스트로 변환 (소스 라벨 + 원본 질문 포함)
        retrieved_texts = []
        for i, doc in enumerate(reranked_docs, 1):
            source_label = self._source_label(doc.collection, doc.metadata)
            original_question = doc.metadata.get('question', '')
            if original_question:
                retrieved_texts.append(
                    f"[{i}] ({source_label}, 유사도:{doc.score:.2f})\n"
                    f"[원본 질문] {original_question}\n"
                    f"[답변 내용] {doc.content}"
                )
            else:
                retrieved_texts.append(f"[{i}] ({source_label}, 유사도:{doc.score:.2f})\n{doc.content}")

        retrieved_context = "\n\n".join(retrieved_texts) if retrieved_texts else "(관련 자료 없음)"

        # intent에 따라 템플릿 선택
        if intent == Intent.EMOTION:
            return t.RESPONSE_GENERATION_EMOTION.format(
                retrieved_context=retrieved_context,
                kg_context=kg_context or "(추가 정보 없음)",
                user_input=user_input,
            )
        return t.RESPONSE_GENERATION.format(
            retrieved_context=retrieved_context,
            kg_context=kg_context or "(추가 정보 없음)",
            user_input=user_input,
        ) + info_gap_block

    def _source_label(self, collection: str, metadata: dict = None) -> str:
        metadata = metadata or {}

        if collection == "pdf_qna":
            return "📖 건강보험심사평가원·대한산부인과학회 등"
        elif collection == "pdf_chunk":
            source = metadata.get("source", "")
            if "한의" in source or "한의표준" in source:
                return "📖 여성 난임 한의표준임상진료지침"
            elif "ASRM" in source:
                return "📖 미국생식의학회(ASRM)"
            return "📖 건강보험심사평가원·대한산부인과학회 등"
        elif collection == "youtube_qna":
            video_id = metadata.get("video_id", "")
            url = f"https://youtu.be/{video_id}" if video_id else ""
            return f"🎥 전문 의료진 YouTube{' | ' + url if url else ''}"
        elif collection == "blog":
            title = metadata.get("title", "")
            url = metadata.get("url", "")
            label = "📝 경험담"
            if title:
                label += f" | {title[:30]}"
            if url:
                label += f" | {url}"
            return label
        elif collection == "web_reference":
            source = metadata.get("source", "")
            return f"🏥 참고자료 | {source}" if source else "🏥 참고자료"
        elif collection == "policy_chunk":
            return "📋 정책자료 | 모자보건사업 안내"
        else:
            return collection
