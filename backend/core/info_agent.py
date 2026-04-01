"""
정보 에이전트 - policy(지원금/보험/비용) 처리

구조화 데이터 매칭 (PolicyEngine) + 벡터 검색 병행
- PolicyEngine: 정확한 수치/절차/금액 → JSON 매칭
- 벡터 검색: 맥락적 보충 정보 → policy_chunk 컬렉션
"""
from config import Intent
from models import UserProfile, RetrievedDocument, ChatSession

from core.llm_client import LLMClient
from core.query_augmenter import QueryAugmenter
from core.retriever import Retriever
from core.reranker import Reranker
from core.knowledge_enricher import KnowledgeEnricher
from core.response_generator import ResponseGenerator
from core.info_gap_detector import InfoGapDetector
from core.policy_engine import PolicyEngine


class InfoAgent:
    """정보 에이전트: 지원금, 보험, 정책 질문 처리

    파이프라인:
    1. PolicyEngine으로 구조화 데이터 조회 (정확한 수치/절차)
    2. 벡터 검색으로 보충 컨텍스트 확보 (policy_chunk 컬렉션 우선)
    3. 두 결과를 합쳐서 LLM에 전달 → 응답 생성
    """

    def __init__(
        self,
        llm: LLMClient,
        query_augmenter: QueryAugmenter,
        retriever: Retriever,
        reranker: Reranker,
        knowledge_enricher: KnowledgeEnricher,
        response_generator: ResponseGenerator,
        info_gap_detector: InfoGapDetector,
    ):
        self.llm = llm
        self.query_augmenter = query_augmenter
        self.retriever = retriever
        self.reranker = reranker
        self.knowledge_enricher = knowledge_enricher
        self.response_generator = response_generator
        self.info_gap_detector = info_gap_detector
        self.policy_engine = PolicyEngine(llm=llm)

        print("[InfoAgent] 초기화 완료 (PolicyEngine 통합)")

    def handle_new(
        self,
        message: str,
        preprocessed: str,
        intent: Intent,
        profile: UserProfile,
        session: ChatSession,
    ) -> dict:
        """새 의도: 구조화 데이터 조회 + 벡터 검색 병행"""

        # ── [1] PolicyEngine: 구조화 데이터 매칭 ──
        policy_result = self.policy_engine.lookup(preprocessed, profile)
        query_type = policy_result["query_type"]
        structured_context = policy_result["structured_context"]
        print(f"  [InfoAgent] PolicyEngine: type={query_type}, found={policy_result['found']}")

        # ── [2] 쿼리 증강 ──
        augmented_query = self.query_augmenter.augment(preprocessed, profile)
        print(f"  [InfoAgent] 쿼리 증강: {augmented_query[:60]}")

        # ── [3] 벡터 검색 ──
        retrieved_docs = self.retriever.search(
            query=augmented_query,
            intent=intent.value,
            profile=profile,
        )
        print(f"  [InfoAgent] 벡터 검색: {len(retrieved_docs)}건")

        # ── [4] 리랭킹 ──
        if retrieved_docs:
            reranked_docs = self.reranker.rerank(
                query=augmented_query,
                user_context=profile.context_summary(),
                documents=retrieved_docs,
            )
        else:
            reranked_docs = []
        print(f"  [InfoAgent] 리랭킹: {len(reranked_docs)}건")

        # ── [5] KG 보강 + 구조화 데이터 병합 ──
        kg_context = self.knowledge_enricher.enrich(
            documents=reranked_docs,
            profile=profile,
            intent=intent.value,
        )

        # 구조화 데이터를 kg_context 앞에 추가 (정확한 수치 우선)
        if structured_context:
            kg_context = f"[구조화 정책 데이터 — {query_type}]\n{structured_context}\n\n{kg_context}"

        # ── [6] 정보 갭 (지역 등 누락 확인) ──
        all_entity_ids = set()
        for doc in reranked_docs:
            all_entity_ids.update(doc.entity_ids)
        info_gap_hint = self.info_gap_detector.detect(
            entity_ids=all_entity_ids,
            profile=profile,
            intent=intent.value,
            user_input=message,
        )

        # 지역 정보 누락 시 추가 힌트
        if query_type in ("지자체_추가", "병원찾기") and not profile.region:
            extra_hint = "사용자의 지역 정보가 없습니다. 지역을 물어보면 더 정확한 안내가 가능합니다."
            info_gap_hint = f"{info_gap_hint}\n{extra_hint}" if info_gap_hint else extra_hint

        # ── [7] 응답 생성 ──
        response = self.response_generator.generate(
            user_input=message,
            intent=intent,
            profile=profile,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint,
        )
        print(f"  [InfoAgent] 응답 생성: {len(response)}자 (type={query_type})")

        sources_used = list(set(doc.source for doc in reranked_docs))
        if structured_context:
            sources_used.append("정책 구조화 데이터")

        return {
            "response": response,
            "augmented_query": augmented_query,
            "retrieved_docs": retrieved_docs,
            "reranked_docs": reranked_docs,
            "kg_context": kg_context,
            "info_gap_hint": info_gap_hint,
            "sources_used": sources_used,
            "context": {
                "reranked_docs": reranked_docs,
                "kg_context": kg_context,
                "entity_ids": all_entity_ids,
                "query_type": query_type,
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
    ) -> dict:
        """꼬리 질문: PolicyEngine 재조회 + 벡터 검색도 수행"""

        kg_context = prev_context.get("kg_context", "")
        entity_ids = prev_context.get("entity_ids", set())
        prev_query_type = prev_context.get("query_type", "일반")

        # 꼬리 질문이 다른 쿼리 타입이면 PolicyEngine 재조회
        new_query_type = self.policy_engine.classify_query_type(preprocessed)
        if new_query_type != "일반" and new_query_type != prev_query_type:
            policy_result = self.policy_engine.lookup(preprocessed, profile)
            if policy_result["found"]:
                kg_context = f"[구조화 정책 데이터 — {new_query_type}]\n{policy_result['structured_context']}\n\n{kg_context}"
                print(f"  [InfoAgent] 꼬리질문 PolicyEngine 재조회: {new_query_type}")

        # 꼬리 질문에서도 벡터 검색 수행 (새 키워드 반영)
        augmented_query = self.query_augmenter.augment(preprocessed, profile)
        print(f"  [InfoAgent] 꼬리질문 쿼리 증강: {augmented_query[:60]}")

        retrieved_docs = self.retriever.search(
            query=augmented_query,
            intent=intent.value,
            profile=profile,
        )
        print(f"  [InfoAgent] 꼬리질문 벡터 검색: {len(retrieved_docs)}건")

        if retrieved_docs:
            reranked_docs = self.reranker.rerank(
                query=augmented_query,
                user_context=profile.context_summary(),
                documents=retrieved_docs,
            )
        else:
            reranked_docs = []
        print(f"  [InfoAgent] 꼬리질문 리랭킹: {len(reranked_docs)}건")

        # 새 검색 결과의 엔티티 추가
        for doc in reranked_docs:
            entity_ids.update(doc.entity_ids)

        info_gap_hint = self.info_gap_detector.detect(
            entity_ids=entity_ids,
            profile=profile,
            intent=intent.value,
            user_input=message,
        )

        response = self.response_generator.generate(
            user_input=message,
            intent=intent,
            profile=profile,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint,
        )
        print(f"  [InfoAgent] 꼬리질문 응답: {len(response)}자")

        sources_used = list(set(doc.source for doc in reranked_docs))

        return {
            "response": response,
            "augmented_query": augmented_query,
            "reranked_docs": reranked_docs,
            "kg_context": kg_context,
            "info_gap_hint": info_gap_hint,
            "sources_used": sources_used,
        }
