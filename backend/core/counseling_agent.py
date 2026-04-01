"""
상담 에이전트 - medical, emotion, out_of_scope 처리

두 가지 모드:
1. handle_new: 풀 파이프라인 (검색 → 리랭킹 → KG → Tool → 정보갭 → 응답생성)
2. handle_followup: 기존 컨텍스트 재사용, 응답 생성만
"""
from typing import Optional
from config import Intent, Weight
from models import UserProfile, RetrievedDocument, ChatSession

from core.llm_client import LLMClient
from core.query_augmenter import QueryAugmenter
from core.retriever import Retriever
from core.reranker import Reranker
from core.knowledge_enricher import KnowledgeEnricher
from core.response_generator import ResponseGenerator
from core.info_gap_detector import InfoGapDetector
from core.tools.tool_router import ToolRouter
from core.tools.drug_search import DrugSearchTool
from core.tools.hospital_search import HospitalSearchTool


class CounselingAgent:
    """상담 에이전트: 의학, 감정, 범위 밖 질문 처리"""

    def __init__(
        self,
        llm: LLMClient,
        query_augmenter: QueryAugmenter,
        retriever: Retriever,
        reranker: Reranker,
        knowledge_enricher: KnowledgeEnricher,
        response_generator: ResponseGenerator,
        info_gap_detector: InfoGapDetector,
        tool_router: ToolRouter = None,
        drug_search: DrugSearchTool = None,
        hospital_search: HospitalSearchTool = None,
    ):
        self.llm = llm
        self.query_augmenter = query_augmenter
        self.retriever = retriever
        self.reranker = reranker
        self.knowledge_enricher = knowledge_enricher
        self.response_generator = response_generator
        self.info_gap_detector = info_gap_detector
        self.tool_router = tool_router
        self.drug_search = drug_search
        self.hospital_search = hospital_search

        print("[CounselingAgent] 초기화 완료")

    def handle_new(
        self,
        message: str,
        preprocessed: str,
        intent: Intent,
        profile: UserProfile,
        session: ChatSession,
        weight: Optional[Weight] = None,
    ) -> dict:
        """새 의도: 풀 파이프라인 실행"""

        # ── 쿼리 증강 (의학 키워드 중심, 프로필 정보 제외) ──
        if intent != Intent.OUT_OF_SCOPE:
            augmented_query = self.query_augmenter.augment_medical(preprocessed, profile)
        else:
            augmented_query = preprocessed
        print(f"  [CounselingAgent] 쿼리 증강: {augmented_query[:60]}")

        # ── 벡터 검색 ──
        if intent != Intent.OUT_OF_SCOPE:
            retrieved_docs = self.retriever.search(
                query=augmented_query,
                intent=intent.value,
                profile=profile,
            )
        else:
            retrieved_docs = []
        print(f"  [CounselingAgent] 벡터 검색: {len(retrieved_docs)}건")

        # ── 리랭킹 ──
        if retrieved_docs:
            reranked_docs = self.reranker.rerank(
                query=augmented_query,
                user_context=profile.context_summary(),
                documents=retrieved_docs,
            )
        else:
            reranked_docs = []
        print(f"  [CounselingAgent] 리랭킹: {len(reranked_docs)}건")

        # ── KG 보강 ──
        kg_context = self.knowledge_enricher.enrich(
            documents=reranked_docs,
            profile=profile,
            intent=intent.value,
        )
        print(f"  [CounselingAgent] KG 보강: {len(kg_context)}자")

        # ── Tool 실행 ──
        tool_context, tool_sources = self._run_tools(message, profile)
        if tool_context:
            kg_context = f"{tool_context}\n\n{kg_context}"

        # ── 정보 갭 탐지 ──
        all_entity_ids = set()
        for doc in reranked_docs:
            all_entity_ids.update(doc.entity_ids)
        info_gap_hint = self.info_gap_detector.detect(
            entity_ids=all_entity_ids,
            profile=profile,
            intent=intent.value,
            user_input=message,
        )
        if info_gap_hint:
            print(f"  [CounselingAgent] 정보 갭: {info_gap_hint[:40]}...")

        # ── 응답 생성 ──
        response = self.response_generator.generate(
            user_input=message,
            intent=intent,
            profile=profile,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint,
            weight=weight,
        )
        print(f"  [CounselingAgent] 응답 생성: {len(response)}자")

        sources_used = list(set(doc.source for doc in reranked_docs))
        sources_used.extend(tool_sources)

        return {
            "response": response,
            "augmented_query": augmented_query,
            "retrieved_docs": retrieved_docs,
            "reranked_docs": reranked_docs,
            "kg_context": kg_context,
            "info_gap_hint": info_gap_hint,
            "sources_used": sources_used,
            # 꼬리질문용 컨텍스트 저장
            "context": {
                "reranked_docs": reranked_docs,
                "kg_context": kg_context,
                "entity_ids": all_entity_ids,
            },
        }

    def handle_followup(
        self,
        message: str,
        preprocessed: str,
        intent: Intent,
        profile: UserProfile,
        session: ChatSession,
        prev_context: dict,
        weight: Optional[Weight] = None,
    ) -> dict:
        """꼬리 질문: 주제 전환 감지 → 전환이면 풀 파이프라인, 아니면 기존 컨텍스트 재사용"""

        # 주제 전환 감지: 기존 검색 결과가 새 메시지를 커버하는지 확인
        reranked_docs = prev_context.get("reranked_docs", [])
        if self._is_topic_shifted(preprocessed, reranked_docs):
            print(f"  [CounselingAgent] 꼬리질문 주제 전환 감지 → 풀 파이프라인 재실행")
            return self.handle_new(
                message=message,
                preprocessed=preprocessed,
                intent=intent,
                profile=profile,
                session=session,
            )

        kg_context = prev_context.get("kg_context", "")
        entity_ids = prev_context.get("entity_ids", set())

        # 꼬리질문에서도 Tool 실행 (새 약물/병원 질문일 수 있음)
        tool_context, tool_sources = self._run_tools(message, profile)
        if tool_context:
            kg_context = f"{tool_context}\n\n{kg_context}"

        # 정보 갭은 매 턴 체크
        info_gap_hint = self.info_gap_detector.detect(
            entity_ids=entity_ids,
            profile=profile,
            intent=intent.value,
            user_input=message,
        )

        # 응답 생성 (기존 검색 결과 + KG + 새 메시지)
        response = self.response_generator.generate(
            user_input=message,
            intent=intent,
            profile=profile,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint,
            weight=weight,
        )
        print(f"  [CounselingAgent] 꼬리질문 응답: {len(response)}자 (검색 스킵)")

        sources = list(set(doc.source for doc in reranked_docs))
        sources.extend(tool_sources)

        return {
            "response": response,
            "augmented_query": "",
            "reranked_docs": reranked_docs,
            "kg_context": kg_context,
            "info_gap_hint": info_gap_hint,
            "sources_used": sources,
        }

    # ── Tool 실행 ──

    def _run_tools(self, message: str, profile: UserProfile) -> tuple[str, list[str]]:
        """
        Tool 라우터로 필요한 tool을 판단하고 실행.
        Returns: (tool_context 문자열, source 목록)
        """
        if not self.tool_router:
            return "", []

        needed_tools = self.tool_router.route(message)
        if not needed_tools:
            return "", []

        context_parts = []
        sources = []

        for tool_name in needed_tools:
            if tool_name == "drug_search" and self.drug_search:
                result = self._run_drug_search(message)
                if result:
                    context_parts.append(result["context"])
                    sources.append(result["source"])

            elif tool_name == "hospital_search" and self.hospital_search:
                result = self._run_hospital_search(message, profile)
                if result:
                    context_parts.append(result["context"])
                    sources.append(result["source"])

        return "\n\n".join(context_parts), sources

    def _run_drug_search(self, message: str) -> Optional[dict]:
        """약물 검색 실행 — 메시지에서 약물명 추출 후 검색"""
        import re

        # 주요 난임 약물명 패턴
        drug_patterns = [
            "세트로타이드", "세트로렐릭스", "가니레릭스", "가니레버",
            "고나도트로핀", "고나도핀", "폴리트롭", "퓨레곤", "메노퓨어",
            "클로미펜", "클로미드", "레트로졸", "페마라",
            "프로게스테론", "유트로게스탄", "듀파스톤", "크리논",
            "오비드렐", "프레그닐",
            "루프론", "데카펩틸",
            "메트포르민", "글루코파지",
            "에스트라디올", "프레마린", "프로기노바",
            "아스피린", "헤파린", "클렉산",
            "엽산", "이노시톨", "코엔자임", "비타민D", "DHEA", "오메가3",
        ]

        found_drugs = []
        for drug in drug_patterns:
            if drug.lower() in message.lower() or drug in message:
                found_drugs.append(drug)

        # 패턴 매칭 안 되면 "약", "주사" 등 일반 키워드로 약물명 추출 시도
        if not found_drugs:
            # 한글 2~8자 + "주사/약/정" 패턴
            matches = re.findall(r'([가-힣]{2,8}(?:주사|주|약|정|캡슐|젤))', message)
            found_drugs = matches[:1]

        if not found_drugs:
            return None

        # 첫 번째 약물로 검색
        drug_name = found_drugs[0]
        result = self.drug_search.search(drug_name)

        if not result["found"]:
            return None

        # 컨텍스트 구성
        context = f"[약물 정보 — {drug_name}]\n출처: {result['source']}\nURL: {result['source_url']}\n"
        if result["summary"]:
            context += f"요약: {result['summary']}\n"
        if result["detail"]:
            context += f"\n{result['detail']}"

        return {"context": context, "source": result["source"]}

    def _run_hospital_search(self, message: str, profile: UserProfile) -> Optional[dict]:
        """병원 검색 실행"""
        # 시술 종류 판단
        treatment_type = ""
        if any(kw in message for kw in ["체외수정", "시험관", "IVF", "ivf"]):
            treatment_type = "ivf"
        elif any(kw in message for kw in ["인공수정", "IUI", "iui"]):
            treatment_type = "iui"

        # 지역: 메시지에서 추출 or 프로필 사용
        region = profile.region or ""

        result = self.hospital_search.search(
            region=region,
            treatment_type=treatment_type,
            include_nearby=True,
        )

        if not result["found"]:
            return None

        # 컨텍스트 구성
        lines = [f"[난임 지정병원 검색 — {region or '전국'}]"]

        if result["hospitals"]:
            lines.append(f"\n📍 {region} 병원 ({len(result['hospitals'])}곳):")
            for h in result["hospitals"]:
                ivf_iui = []
                if h["체외수정"]:
                    ivf_iui.append("체외수정")
                if h["인공수정"]:
                    ivf_iui.append("인공수정")
                lines.append(
                    f"  - {h['병원명']} ({h['종별']}, 의사 {h['의사수']}명)"
                    f"\n    {h['주소']}"
                    f"\n    ☎ {h['전화번호']}"
                    f" | {', '.join(ivf_iui)}"
                    f"{' | 🌐 ' + h['홈페이지'] if h['홈페이지'] else ''}"
                )

        if result["nearby_hospitals"]:
            lines.append(f"\n📍 인근 지역 병원 ({len(result['nearby_hospitals'])}곳):")
            for h in result["nearby_hospitals"]:
                lines.append(
                    f"  - {h['병원명']} ({h['시군구']}, 의사 {h['의사수']}명)"
                    f"\n    ☎ {h['전화번호']}"
                )

        context = "\n".join(lines)
        return {"context": context, "source": "HIRA 난임 지정병원 데이터"}

    # ── 주제 전환 감지 ──

    def _is_topic_shifted(self, preprocessed: str, prev_docs: list[RetrievedDocument]) -> bool:
        """기존 검색 결과와 다른 주제인지 감지"""
        if not prev_docs:
            return True

        import re
        new_keywords = set(re.findall(r'[가-힣]{2,}', preprocessed))
        stop_words = {"그런데", "그리고", "근데", "혹시", "그거", "그건", "어떤", "이거", "저거",
                      "얼마나", "언제", "어디", "어떻게", "왜", "뭐", "정도", "같은", "대해",
                      "해도", "되나요", "인가요", "건가요", "할까요", "볼까요", "싶어요", "있어요",
                      "없어요", "했어요", "거예요", "될까요", "같아요", "것도", "하고", "해서"}
        new_keywords -= stop_words
        if not new_keywords:
            return False

        prev_text = " ".join(doc.content[:200] for doc in prev_docs)

        matched = sum(1 for kw in new_keywords if kw in prev_text)
        match_ratio = matched / len(new_keywords) if new_keywords else 1.0

        if match_ratio < 0.2:
            print(f"  [CounselingAgent] 주제 전환: 매칭 {matched}/{len(new_keywords)} = {match_ratio:.0%}")
            return True
        return False
