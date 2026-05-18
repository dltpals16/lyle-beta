"""
Supervisor — 의도 판별 + 라우팅 + 세션 관리

역할:
1. 위기 체크 (룰 기반)
2. 용어 전처리 (룰 기반)
3. 의도 판별 (LLM 1회: medical/emotion/policy/out_of_scope)
4. 라우팅:
   - medical + emotion → CareAgent
   - policy → PolicyAgent
   - out_of_scope → 직접 응답
5. 세션/프로필 업데이트

⚠ Supervisor는 경중(light/heavy) 판별 안 함 — 각 에이전트가 자체 판별
"""
from dataclasses import dataclass, field
from typing import Optional
from config import Intent
from models import UserProfile, ChatSession, PipelineResult
from core.llm_client import LLMClient
from core.term_preprocessor import TermPreprocessor
from core.intent_classifier import IntentClassifier
from core.safety_filter import SafetyFilter
from core.care_agent import CareAgent
from core.policy_agent import PolicyAgent
from core.recommend_agent import RecommendAgent

from prompts.templates import PROMPT_OUT_OF_SCOPE, SYSTEM_BASE
from prompts import get_templates


OUT_OF_SCOPE_SYSTEM = "당신은 난임 상담 챗봇 라일입니다. 난임과 무관한 질문에 간결하게 응답하세요."

# OUT_OF_SCOPE_PROMPT는 templates에서 가져옴 (하드코딩 제거)


@dataclass
class ConversationState:
    """사용자별 대화 상태"""
    current_intent: Optional[str] = None
    followup_count: int = 0

    def reset(self):
        self.current_intent = None
        self.followup_count = 0


class Supervisor:
    """라우터 에이전트 — 의도 판별, 라우팅, 세션 관리"""

    def __init__(
        self,
        llm: LLMClient,
        term_preprocessor: TermPreprocessor,
        intent_classifier: IntentClassifier,
        safety_filter: SafetyFilter,
        care_agent: CareAgent,
        policy_agent: PolicyAgent,
        recommend_agent: RecommendAgent = None,
    ):
        self.llm = llm
        self.term_preprocessor = term_preprocessor
        self.intent_classifier = intent_classifier
        self.safety_filter = safety_filter
        self.care_agent = care_agent
        self.policy_agent = policy_agent
        self.recommend_agent = recommend_agent

        self.states: dict[str, ConversationState] = {}
        print("[Supervisor] 초기화 완료")

    def chat(
        self,
        user_id: str,
        message: str,
        profile: UserProfile,
        session: ChatSession,
        status_callback=None,
    ) -> PipelineResult:
        """메인 대화 처리"""
        result = PipelineResult(
            user_input=message,
            preprocessed_input="",
            intent="",
            augmented_query="",
        )
        state = self._get_state(user_id)

        # ── [Step 0] 위기 체크 (룰 기반) ──
        crisis = self.safety_filter.check_crisis(message)
        if crisis["is_crisis"]:
            response = self.safety_filter.get_crisis_response()
            session.add_message("user", message, intent="emotion")
            session.add_message("assistant", response)
            result.intent = "emotion"
            result.response = response
            result.safety_flags = [f"위기 키워드 감지: {crisis['keywords_found']}"]
            state.reset()
            return result

        # ── [Step 1] 용어 전처리 ──
        preprocessed = self.term_preprocessor.process(message)
        result.preprocessed_input = preprocessed
        print(f"[Supervisor] 전처리: {message[:40]} → {preprocessed[:40]}")

        # ── [Step 2] 의도 판별 (LLM 1회) ──
        recent_msgs = self._format_recent_messages(session)
        recent_history = session.get_recent_history(n=4)
        intent, weight = self.intent_classifier.classify(
            user_input=preprocessed,
            user_context=profile.context_summary(),
            recent_messages=recent_msgs,
            history=recent_history,
            mode=getattr(profile, 'mode', 'medical'),
        )
        state.current_intent = intent.value
        result.intent = intent.value
        weight_str = weight.value if weight else ""
        print(f"[Supervisor] 의도: {intent.value}, 경중: {weight_str or 'N/A'}")

        # ── [Step 2.5] out_of_scope 재확인 (히스토리 있으면 이전 대화 연장인지 체크) ──
        if intent == Intent.OUT_OF_SCOPE and recent_history:
            try:
                recheck_prompt = f"""이전 대화 맥락:
{chr(10).join(f'[{m["role"]}] {m["content"][:100]}' for m in recent_history[-4:])}

현재 메시지: {preprocessed}

이 메시지가 이전 대화의 연장인가요, 완전히 다른 주제인가요?
- 이전 대화와 관련이 있거나, 이전 응답에 대한 후속/재요청이면: "연장"
- 이전 대화와 무관한 새 주제면: "새주제"
한 단어로만 답하세요."""
                recheck = self.llm.generate(
                    system_prompt="대화 맥락 판단기입니다. '연장' 또는 '새주제' 중 하나만 답하세요.",
                    user_message=recheck_prompt,
                    max_tokens=10,
                )
                if "연장" in recheck:
                    # 이전 intent로 복원
                    last_intents = [m.intent for m in reversed(session.messages) if m.intent]
                    if last_intents:
                        intent = Intent(last_intents[0])
                        weight = Weight.HEAVY
                        print(f"[Supervisor] out_of_scope → 이전 대화 연장으로 재분류: {intent.value}")
                    else:
                        intent = Intent.MEDICAL
                        weight = Weight.HEAVY
                        print(f"[Supervisor] out_of_scope → 이전 대화 연장 (기본 medical)")
                    result.intent = intent.value
                else:
                    print(f"[Supervisor] out_of_scope 확정 (새 주제)")
            except Exception as e:
                print(f"[Supervisor] out_of_scope 재확인 오류: {e}")

        # ── [Step 3] 라우팅 ──
        if intent == Intent.OUT_OF_SCOPE:
            # Supervisor가 직접 간단 응답
            agent_result = self._handle_out_of_scope(preprocessed, profile)
        elif intent == Intent.POLICY:
            print(f"[Supervisor] → PolicyAgent ({weight_str})")
            agent_result = self.policy_agent.run(
                preprocessed=preprocessed,
                profile=profile,
                session=session,
                weight=weight_str,
            )
        elif intent == Intent.RECOMMENDATION and self.recommend_agent is not None:
            print(f"[Supervisor] → RecommendAgent")
            agent_result = self.recommend_agent.run(
                preprocessed=preprocessed,
                profile=profile,
                session=session,
            )
        else:
            # MEDICAL, EMOTION (또는 RECOMMENDATION인데 에이전트 없을 때 fallback)
            print(f"[Supervisor] → CareAgent ({intent.value}, {weight_str})")
            agent_result = self.care_agent.run(
                preprocessed=preprocessed,
                intent=intent,
                profile=profile,
                session=session,
                weight=weight_str,
                status_callback=status_callback,
            )

        # ── 결과 병합 ──
        result.response = agent_result["response"]
        result.links = agent_result.get("links", [])
        result.doctor_questions = agent_result.get("doctor_questions", [])
        result.safety_flags = agent_result.get("safety_flags", [])
        result.reranked_docs = agent_result.get("reranked_docs", [])
        result.kg_context = agent_result.get("kg_context", "")
        result.sources_used = agent_result.get("sources_used", [])
        result.suggested_replies = agent_result.get("suggested_replies", [])

        # ── 프로필 업데이트 (응답 생성 시 감지된 것) — 게스트는 스킵 ──
        profile_updates = agent_result.get("profile_updates", {})
        is_guest = user_id.startswith("guest_")
        if profile_updates and not is_guest:
            self._apply_profile_updates(profile, profile_updates)
            # 실제 변경된 것만 result에 반영 (중복 제거 후)
            if profile_updates.get("fields") or profile_updates.get("notes"):
                result.profile_updates = profile_updates

        # ── 세션 저장 ──
        session.add_message("user", message, intent=intent.value)
        session.add_message("assistant", result.response, links=result.links or [], sources=result.sources_used or [], profile_updates=result.profile_updates or {})

        return result

    def _handle_out_of_scope(self, preprocessed: str, profile: UserProfile) -> dict:
        """out_of_scope: Supervisor가 직접 간단 응답 — templates에서 프롬프트 가져옴"""
        from prompts import get_templates
        mode = getattr(profile, 'mode', 'medical')
        t = get_templates(mode)
        system_prompt = t.SYSTEM_BASE.format(user_context=profile.context_summary())
        user_prompt = t.PROMPT_OUT_OF_SCOPE.format(user_input=preprocessed)
        response = self.llm.generate_light(prompt=user_prompt, max_tokens=150, system_prompt=system_prompt)
        print(f"[Supervisor] out_of_scope 직접 응답")
        return {
            "response": response,
            "links": [],
            "doctor_questions": [],
            "safety_flags": [],
            "profile_updates": {},
            "sources_used": [],
        }

    def _apply_profile_updates(self, profile: UserProfile, updates: dict):
        """응답 생성에서 감지된 프로필 업데이트 적용"""
        from datetime import datetime
        import uuid

        # 구조화 필드 업데이트
        fields = updates.get("fields", {})
        valid_fields = {
            "treatment_stage", "current_phase", "embryo_grade",
            "protocol", "treatment_cycle", "amh", "diagnoses",
            "infertility_duration", "marriage_status", "dual_income",
            "partner_diagnosis", "frozen_embryo_count", "current_medications",
        }
        # 리스트 타입 필드 — 문자열이 오면 리스트로 변환
        list_fields = {"diagnoses", "current_medications"}

        actually_changed = {}
        for key, value in fields.items():
            if key in valid_fields and value and hasattr(profile, key):
                current = getattr(profile, key)
                if key in list_fields:
                    if isinstance(value, str):
                        value = [v.strip() for v in value.split(",")]
                    existing = getattr(profile, key, [])
                    merged = list(set(existing + value))
                    if set(merged) != set(existing):
                        setattr(profile, key, merged)
                        actually_changed[key] = merged
                        print(f"  [Supervisor] 프로필 필드 업데이트: {key} = {merged}")
                else:
                    if current != value:
                        setattr(profile, key, value)
                        actually_changed[key] = value
                        print(f"  [Supervisor] 프로필 필드 업데이트: {key} = {value}")
                    else:
                        print(f"  [Supervisor] 프로필 필드 변경 없음 (이미 동일): {key} = {value}")
        # 실제 변경된 필드만 남기기
        updates["fields"] = actually_changed

        # notes 추가 (기존 notes와 중복 체크)
        from firebase_config import _is_similar
        notes = updates.get("notes", [])
        existing_note_contents = [n.get("content", "") for n in profile.notes if isinstance(n, dict)]
        for note_text in notes:
            if not note_text or not note_text.strip():
                continue
            n_clean = note_text.strip()
            if any(n_clean == ex or _is_similar(n_clean, ex) for ex in existing_note_contents):
                print(f"  [Supervisor] 채팅 기억 중복 스킵: {n_clean}")
                continue
            profile.notes.append({
                "id": str(uuid.uuid4())[:8],
                "content": n_clean,
                "created_at": datetime.now().isoformat(),
            })
            existing_note_contents.append(n_clean)
            print(f"  [Supervisor] 채팅 기억 추가: {n_clean}")

        if fields or notes:
            profile.updated_at = datetime.now()

    def _get_state(self, user_id: str) -> ConversationState:
        if user_id not in self.states:
            self.states[user_id] = ConversationState()
        return self.states[user_id]

    def _format_recent_messages(self, session: ChatSession, n: int = 3) -> str:
        history = session.get_recent_history(n)
        if not history:
            return ""
        lines = []
        for msg in history[-n * 2:]:
            role = "사용자" if msg["role"] == "user" else "라일"
            lines.append(f"{role}: {msg['content'][:120]}")
        return "\n".join(lines)

    def reset_state(self, user_id: str):
        if user_id in self.states:
            del self.states[user_id]
