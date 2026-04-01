"""
PolicyAgent — policy(지원금/보험/비용) 처리 (LangGraph 서브그래프)

그래프 구조:
  classify_weight → [light] → policy_lookup → generate_response
                 → [heavy] → augment_query → retrieve → rerank → policy_lookup → generate_response
  generate_response → safety_check → END
"""
import os
from typing import TypedDict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from config import Intent, Weight, OPENAI_MODEL_LIGHT
from models import UserProfile, ChatSession
from core.query_augmenter import QueryAugmenter
from core.retriever import Retriever
from core.reranker import Reranker
from core.knowledge_enricher import KnowledgeEnricher
from core.response_generator import ResponseGenerator
from core.safety_filter import SafetyFilter
from core.info_gap_detector import InfoGapDetector
from core.policy_engine import PolicyEngine


CLASSIFY_WEIGHT_POLICY_PROMPT = """난임 정책/지원금 챗봇에서 아래 질문이 개인 맞춤 조회가 필요한지(heavy) 아니면 일반 정책 안내로 충분한지(light) 판단하세요.

## 사용자 정보
{user_context}

## 질문
{user_input}

## 판단 기준
light: 일반적인 난임 지원 제도 설명, 신청 방법 개요, 서류 목록 등 개인 조건과 무관한 정보
heavy: 특정 금액, 지역별 추가 지원, 회차별 금액, 개인 소득/혼인 상태에 따른 맞춤 조회

light 또는 heavy 중 하나만 출력하세요.

판단:"""


class PolicyAgentState(TypedDict):
    preprocessed: str
    profile: Any
    messages: list
    session: Any
    weight: str
    search_queries: list
    retrieved_docs: list
    reranked_docs: list
    policy_context: str
    kg_context: str
    info_gap_hint: str
    response_text: str
    links: list
    doctor_questions: list
    safety_flags: list
    profile_updates: dict
    sources_used: list


class PolicyAgent:
    """정책/지원금 처리 에이전트 (LangGraph 서브그래프)"""

    def __init__(
        self,
        query_augmenter: QueryAugmenter,
        retriever: Retriever,
        reranker: Reranker,
        knowledge_enricher: KnowledgeEnricher,
        response_generator: ResponseGenerator,
        safety_filter: SafetyFilter,
        info_gap_detector: InfoGapDetector,
        llm_client=None,
    ):
        self.query_augmenter = query_augmenter
        self.retriever = retriever
        self.reranker = reranker
        self.knowledge_enricher = knowledge_enricher
        self.response_generator = response_generator
        self.safety_filter = safety_filter
        self.info_gap_detector = info_gap_detector
        self.policy_engine = PolicyEngine(llm=llm_client)

        self.llm_light = ChatOpenAI(
            model=OPENAI_MODEL_LIGHT,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )

        self.graph = self._build_graph()
        print("[PolicyAgent] LangGraph 초기화 완료")

    def _build_graph(self):
        workflow = StateGraph(PolicyAgentState)

        workflow.add_node("classify_weight", self._classify_weight)
        workflow.add_node("policy_lookup_light", self._policy_lookup_light)
        workflow.add_node("augment_query", self._augment_query)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("rerank", self._rerank)
        workflow.add_node("policy_lookup_heavy", self._policy_lookup_heavy)
        workflow.add_node("generate_response", self._generate_response)

        workflow.set_entry_point("classify_weight")
        workflow.add_conditional_edges(
            "classify_weight",
            self._route_by_weight,
            {"light": "policy_lookup_light", "heavy": "augment_query"},
        )

        # light 경로
        workflow.add_edge("policy_lookup_light", "generate_response")

        # heavy 경로
        workflow.add_edge("augment_query", "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "policy_lookup_heavy")
        workflow.add_edge("policy_lookup_heavy", "generate_response")

        workflow.add_edge("generate_response", END)

        return workflow.compile()

    def _classify_weight(self, state: PolicyAgentState) -> dict:
        # Supervisor가 이미 분류한 weight가 있으면 스킵
        if state["weight"] in ("light", "heavy"):
            print(f"  [PolicyAgent:classify_weight] Supervisor 전달값 → {state['weight']}")
            return {}

        profile = state["profile"]
        user_context = profile.context_summary() if hasattr(profile, 'context_summary') else ""

        prompt = CLASSIFY_WEIGHT_POLICY_PROMPT.format(
            user_context=user_context,
            user_input=state["preprocessed"],
        )
        response = self.llm_light.invoke(prompt)
        text = response.content.strip().lower()
        weight = "light" if "light" in text else "heavy"
        print(f"  [PolicyAgent:classify_weight] → {weight}")
        return {"weight": weight}

    def _route_by_weight(self, state: PolicyAgentState) -> str:
        return state["weight"]

    def _policy_lookup_light(self, state: PolicyAgentState) -> dict:
        """light 경로: PolicyEngine 기본 조회"""
        profile = state["profile"]
        policy_result = self.policy_engine.lookup(state["preprocessed"], profile)
        structured_context = policy_result.get("structured_context", "")
        print(f"  [PolicyAgent:policy_lookup_light] found={policy_result.get('found', False)}")
        return {
            "policy_context": structured_context,
            "kg_context": structured_context,
            "info_gap_hint": "",
        }

    def _augment_query(self, state: PolicyAgentState) -> dict:
        profile = state["profile"]
        augmented = self.query_augmenter.augment(state["preprocessed"], profile)
        queries = [q.strip().lstrip("-•→").strip() for q in augmented.split("\n") if q.strip()]
        if not queries:
            queries = [state["preprocessed"]]
        print(f"  [PolicyAgent:augment_query] {len(queries)}개 쿼리")
        return {"search_queries": queries}

    def _retrieve(self, state: PolicyAgentState) -> dict:
        profile = state["profile"]
        queries = state["search_queries"]
        all_docs = []
        seen_ids = set()

        for query in queries:
            docs = self.retriever.search(query=query, intent="policy", profile=profile)
            for doc in docs:
                doc_id = doc.content[:100]
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_docs.append(doc)

        print(f"  [PolicyAgent:retrieve] {len(all_docs)}건")
        return {"retrieved_docs": all_docs}

    def _rerank(self, state: PolicyAgentState) -> dict:
        profile = state["profile"]
        docs = state["retrieved_docs"]
        queries = state["search_queries"]
        if not docs:
            return {"reranked_docs": []}
        primary_query = queries[0] if queries else state["preprocessed"]
        reranked = self.reranker.rerank(
            query=primary_query,
            user_context=profile.context_summary() if hasattr(profile, 'context_summary') else "",
            documents=docs,
        )
        print(f"  [PolicyAgent:rerank] {len(docs)} → {len(reranked)}건")
        return {"reranked_docs": reranked}

    def _policy_lookup_heavy(self, state: PolicyAgentState) -> dict:
        """heavy 경로: PolicyEngine 맞춤 조회 + 벡터 검색 결과 병합"""
        profile = state["profile"]
        reranked_docs = state["reranked_docs"]

        policy_result = self.policy_engine.lookup(state["preprocessed"], profile)
        query_type = policy_result.get("query_type", "일반")
        structured_context = policy_result.get("structured_context", "")

        kg_context = self.knowledge_enricher.enrich(
            documents=reranked_docs,
            profile=profile,
            intent="policy",
        )

        if structured_context:
            kg_context = f"[구조화 정책 데이터 — {query_type}]\n{structured_context}\n\n{kg_context}"

        # 정보 갭 탐지
        all_entity_ids = set()
        for doc in reranked_docs:
            all_entity_ids.update(doc.entity_ids)
        info_gap_hint = self.info_gap_detector.detect(
            entity_ids=all_entity_ids,
            profile=profile,
            intent="policy",
            user_input=state["preprocessed"],
        )
        if query_type in ("지자체_추가", "병원찾기") and not profile.region:
            extra = "사용자의 지역 정보가 없습니다. 지역을 물어보면 더 정확한 안내가 가능합니다."
            info_gap_hint = f"{info_gap_hint}\n{extra}" if info_gap_hint else extra

        print(f"  [PolicyAgent:policy_lookup_heavy] type={query_type}, found={policy_result.get('found', False)}")
        return {
            "policy_context": structured_context,
            "kg_context": kg_context,
            "info_gap_hint": info_gap_hint or "",
        }

    def _generate_response(self, state: PolicyAgentState) -> dict:
        profile = state["profile"]
        session = state["session"]
        reranked_docs = state.get("reranked_docs", [])
        kg_context = state.get("kg_context", "")
        info_gap_hint = state.get("info_gap_hint", "")
        weight = state.get("weight", "heavy")

        try:
            weight_enum = Weight(weight)
        except ValueError:
            weight_enum = Weight.HEAVY

        response_text, profile_updates = self.response_generator.generate(
            user_input=state["preprocessed"],
            intent=Intent.POLICY,
            profile=profile,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint if info_gap_hint else None,
            weight=weight_enum,
        )

        # sources 수집 (blog는 카드로만 표시하므로 텍스트 출처에서 제외)
        text_sources = []
        for doc in reranked_docs:
            if not hasattr(doc, 'source') or not doc.source:
                continue
            if doc.collection == "blog":
                continue
            if doc.collection == "youtube_qna":
                text_sources.append("전문 의료진 YouTube")
            else:
                text_sources.append(doc.source)
        sources_used = list(set(text_sources))

        print(f"  [PolicyAgent:generate_response] 응답 {len(response_text)}자, sources {len(sources_used)}개")
        return {"response_text": response_text, "links": [], "doctor_questions": [], "profile_updates": profile_updates, "sources_used": sources_used}

    def _safety_check(self, state: PolicyAgentState) -> dict:
        safety = self.safety_filter.check_response(state["response_text"], "policy")
        flags = safety.get("flags", [])
        if flags:
            print(f"  [PolicyAgent:safety_check] 경고: {flags}")
        return {"safety_flags": flags}

    def _extract_doctor_questions(self, state: PolicyAgentState) -> dict:
        """응답에서 '다음 진료 때 물어볼 질문'을 LLM light로 추출 (safety_check과 병렬)"""
        response_text = state["response_text"]

        # 진료 관련 키워드가 없으면 스킵 (불필요한 LLM 호출 방지)
        trigger_keywords = ["진료", "선생님", "여쭤", "확인해", "물어보", "상의", "주치의", "상담", "담당"]
        if not any(kw in response_text for kw in trigger_keywords):
            return {"doctor_questions": []}

        user_input = state.get("preprocessed", "")
        prompt = f"""아래 AI 응답에서, 의사에게 꼭 확인이 필요한 내용만 추출하세요.

## 사용자 질문
{user_input}

## AI 응답
{response_text}

## 추출 규칙 (엄격하게 적용)
1. AI가 이미 충분히 답한 내용은 추출하지 않음
2. **개인 맞춤 판단이 필요한 것만** 추출 (약물 용량, 검사 수치 해석, 시술 일정 조정 등)
3. "선생님께 확인해보세요" 같은 습관적 멘트는 무시 — 구체적 이유가 있는 진료 연결만 추출
4. 진료 연결 내용이 없으면 반드시 빈 리스트 반환
5. **최대 1~2개**만. 없으면 빈 리스트.
6. **체크리스트 말투**: "~여쭤보기", "~확인하기" (짧게)
   예: "에스트로겐 용량 조절 필요한지 확인하기"
   예: "내막 두께에 따른 이식 일정 여쭤보기"

## 출력 형식 (JSON 리스트만 출력, 다른 텍스트 금지)
["질문1"]"""

        try:
            result = self.llm_light.invoke(prompt)
            text = result.content.strip()

            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            import json
            questions = json.loads(text)
            if not isinstance(questions, list):
                questions = []
            questions = [q for q in questions if isinstance(q, str) and q.strip()]

            if questions:
                print(f"  [PolicyAgent:extract_doctor_questions] {len(questions)}개 추출: {questions}")
            else:
                print("  [PolicyAgent:extract_doctor_questions] 추출 없음")

            return {"doctor_questions": questions}

        except Exception as e:
            print(f"  [PolicyAgent:extract_doctor_questions] 파싱 실패: {e}")
            return {"doctor_questions": []}

    def run(
        self,
        preprocessed: str,
        profile: UserProfile,
        session: ChatSession,
        weight: str = "",
    ) -> dict:
        """PolicyAgent 실행 — Supervisor에서 호출 (weight는 Supervisor가 전달)"""
        initial_state = {
            "preprocessed": preprocessed,
            "profile": profile,
            "messages": session.get_recent_history(10),
            "session": session,
            "weight": weight,
            "search_queries": [],
            "retrieved_docs": [],
            "reranked_docs": [],
            "policy_context": "",
            "kg_context": "",
            "info_gap_hint": "",
            "response_text": "",
            "links": [],
            "doctor_questions": [],
            "safety_flags": [],
            "profile_updates": {},
            "sources_used": [],
        }

        result = self.graph.invoke(initial_state)

        return {
            "response": result["response_text"],
            "links": result.get("links", []),
            "doctor_questions": result.get("doctor_questions", []),
            "safety_flags": result.get("safety_flags", []),
            "profile_updates": result.get("profile_updates", {}),
            "weight": result.get("weight", ""),
            "reranked_docs": result.get("reranked_docs", []),
            "kg_context": result.get("kg_context", ""),
            "sources_used": result.get("sources_used", []),
        }
