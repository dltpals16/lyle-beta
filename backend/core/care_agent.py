"""
CareAgent — medical + emotion 처리 (LangGraph 서브그래프)

그래프 구조:
  classify_weight → [light] → inmemory_lookup → generate_response
                  → [heavy] → augment_query → retrieve → rerank → kg_enrich → generate_response
  generate_response → safety_check → END
"""
import os
from typing import TypedDict, Optional, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from config import Intent, Weight, OPENAI_MODEL_MAIN, OPENAI_MODEL_LIGHT
from models import UserProfile, ChatSession, RetrievedDocument
from core.query_augmenter import QueryAugmenter
from core.retriever import Retriever
from core.reranker import Reranker
from core.knowledge_enricher import KnowledgeEnricher
from core.response_generator import ResponseGenerator
from core.safety_filter import SafetyFilter
from core.info_gap_detector import InfoGapDetector


# ── Weight 판별 프롬프트 (경량) ─────────────────────────────
CLASSIFY_WEIGHT_PROMPT = """난임 챗봇에서 아래 질문이 벡터 DB 검색이 필요한지(heavy) 아니면 인메모리 데이터(KG, 타임라인, 트리플, 용어)만으로 답할 수 있는지(light) 판단하세요.

## 사용자 정보
{user_context}

## 질문
{user_input}

## 판단 기준
light (인메모리 데이터만으로 답변 가능):
- 의학 용어 정의, 시술 과정/단계 설명, 일반 개념
- 시술 타임라인, 일정, 흐름 질문
- 예: "AMH가 뭐야?", "체외수정 과정이 어떻게 돼?", "난임 기준이 뭐야?"

heavy (벡터 검색 필요 — 전문가 영상, 가이드북, 경험담 등 추가 근거 필요):
- 특정 증상, 부작용, 수치 해석 — 출처 있는 근거 필요
- 사용자 개인 상황(단계, 회차, 프로토콜)에 맞춘 답변 필요
- 감정 지지 — 경험담/블로그 참고 필요
- 영양제, 식이, 생활습관 추천/조언 — 전문가 근거 필요
- "~에 좋은 것", "~에 도움이 되는 것", "~해도 되나요?" 등 추천/허용 여부 질문
- 예: "과배란 후 생리가 줄었어요", "배아 이식 후 주의사항", "너무 힘들어요", "다낭성에 좋은 영양제?", "이식 후 운동해도 돼?"

light 또는 heavy 중 하나만 출력하세요.

판단:"""


class CareAgentState(TypedDict):
    # 입력
    preprocessed: str
    intent: str          # "medical" 또는 "emotion"
    profile: Any         # UserProfile 객체
    messages: list
    session: Any         # ChatSession 객체
    # 경중 판별
    weight: str          # "light" | "heavy"
    # 쿼리 증강 (heavy)
    search_queries: list
    # 검색 결과 (heavy)
    retrieved_docs: list
    reranked_docs: list
    # 인메모리 (light)
    inmemory_context: str
    # KG 보강
    kg_context: str
    # info gap hint
    info_gap_hint: str
    # 출력
    response_text: str
    links: list
    doctor_questions: list
    safety_flags: list
    profile_updates: dict
    sources_used: list
    suggested_replies: list
    status_callback: Optional[Any]   # Optional[Callable[[str], None]]


class CareAgent:
    """의학 + 감정 처리 에이전트 (LangGraph 서브그래프)"""

    def __init__(
        self,
        query_augmenter: QueryAugmenter,
        retriever: Retriever,
        reranker: Reranker,
        knowledge_enricher: KnowledgeEnricher,
        response_generator: ResponseGenerator,
        safety_filter: SafetyFilter,
        info_gap_detector: InfoGapDetector,
        tool_router=None,
        drug_search=None,
        hospital_search=None,
    ):
        self.query_augmenter = query_augmenter
        self.retriever = retriever
        self.reranker = reranker
        self.knowledge_enricher = knowledge_enricher
        self.response_generator = response_generator
        self.safety_filter = safety_filter
        self.info_gap_detector = info_gap_detector
        self.tool_router = tool_router
        self.drug_search = drug_search
        self.hospital_search = hospital_search

        self.llm_light = ChatOpenAI(
            model=OPENAI_MODEL_LIGHT,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )

        self.graph = self._build_graph()
        print("[CareAgent] LangGraph 초기화 완료")

    def _build_graph(self):
        workflow = StateGraph(CareAgentState)

        # 노드 등록
        workflow.add_node("classify_weight", self._classify_weight)
        workflow.add_node("inmemory_lookup", self._inmemory_lookup)
        workflow.add_node("augment_query", self._augment_query)
        workflow.add_node("retrieve", self._retrieve)
        workflow.add_node("rerank", self._rerank)
        workflow.add_node("kg_enrich", self._kg_enrich)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("safety_check", self._safety_check)
        workflow.add_node("extract_doctor_questions", self._extract_doctor_questions)
        workflow.add_node("generate_suggestions", self._generate_suggestions)

        # 시작점
        workflow.set_entry_point("classify_weight")

        # 경중 분기
        workflow.add_conditional_edges(
            "classify_weight",
            self._route_by_weight,
            {"light": "inmemory_lookup", "heavy": "augment_query"},
        )

        # light 경로
        workflow.add_edge("inmemory_lookup", "generate_response")

        # heavy 경로
        workflow.add_edge("augment_query", "retrieve")
        workflow.add_edge("retrieve", "rerank")
        workflow.add_edge("rerank", "kg_enrich")
        workflow.add_edge("kg_enrich", "generate_response")

        # 공통 후처리 (safety_check + extract_doctor_questions + generate_suggestions 병렬)
        workflow.add_edge("generate_response", "safety_check")
        workflow.add_edge("generate_response", "extract_doctor_questions")
        workflow.add_edge("generate_response", "generate_suggestions")
        workflow.add_edge("safety_check", END)
        workflow.add_edge("extract_doctor_questions", END)
        workflow.add_edge("generate_suggestions", END)

        return workflow.compile()

    # ─── 상태 메시지 emit ────────────────────────────────
    def _emit(self, state: CareAgentState, message: str):
        cb = state.get("status_callback")
        if cb:
            cb(message)

    # ─── 노드 구현 ───────────────────────────────────────

    def _classify_weight(self, state: CareAgentState) -> dict:
        """경중 판별: Supervisor에서 전달받았으면 스킵"""
        # Supervisor가 이미 분류한 weight가 있으면 그대로 사용
        if state["weight"] in ("light", "heavy"):
            print(f"  [CareAgent:classify_weight] Supervisor 전달값 → {state['weight']}")
            return {}

        profile = state["profile"]
        user_context = profile.context_summary() if hasattr(profile, 'context_summary') else ""

        prompt = CLASSIFY_WEIGHT_PROMPT.format(
            user_context=user_context,
            user_input=state["preprocessed"],
        )

        response = self.llm_light.invoke(prompt)
        text = response.content.strip().lower()

        weight = "light" if "light" in text else "heavy"
        print(f"  [CareAgent:classify_weight] → {weight}")
        return {"weight": weight}

    def _route_by_weight(self, state: CareAgentState) -> str:
        return state["weight"]

    def _inmemory_lookup(self, state: CareAgentState) -> dict:
        """light 경로: KG/timeline/triples에서 인메모리 데이터 조회"""
        profile = state["profile"]
        intent = state["intent"]

        # KnowledgeEnricher에서 인메모리 데이터 추출 (검색 결과 없이 프로필 기반으로)
        kg_context = self.knowledge_enricher.enrich(
            documents=[],
            profile=profile,
            intent=intent,
            user_message=state.get("preprocessed", ""),
        )

        print(f"  [CareAgent:inmemory_lookup] KG 컨텍스트 {len(kg_context)}자")

        # KG 컨텍스트 부족 판단:
        # 1) 200자 미만 OR
        # 2) "관련 의학 정보" 섹션 없음 (엔티티 매칭 실패 → 타임라인만 있는 경우)
        has_medical_info = "### 관련 의학 정보" in kg_context
        if len(kg_context) < 200 or not has_medical_info:
            reason = f"{len(kg_context)}자 < 200" if len(kg_context) < 200 else "관련 엔티티 없음"
            print(f"  [CareAgent:inmemory_lookup] KG 부족 ({reason}) → heavy 승격, RAG 실행")
            # augment → retrieve → rerank 직접 실행
            aug_result = self._augment_query(state)
            state_with_queries = {**state, **aug_result}
            ret_result = self._retrieve(state_with_queries)
            state_with_docs = {**state_with_queries, **ret_result}
            rerank_result = self._rerank(state_with_docs)
            return {
                **rerank_result,
                "kg_context": kg_context,
                "info_gap_hint": "",
                "weight": "heavy",
            }

        return {
            "inmemory_context": kg_context,
            "kg_context": kg_context,
            "info_gap_hint": "",
        }

    def _augment_query(self, state: CareAgentState) -> dict:
        """heavy 경로: 멀티 쿼리 생성"""
        self._emit(state, "관련 자료를 검색하고 있어요...")
        profile = state["profile"]
        preprocessed = state["preprocessed"]
        intent = state["intent"]
        session = state.get("session")

        # 최근 대화 맥락 추출 (LLM이 후속/새주제 판단)
        recent_context = ""
        if session:
            history = session.get_recent_history(n=2)
            if history and len(history) >= 2:
                prev_msgs = [m for m in history[:-1] if m.get("role") == "user"]
                if prev_msgs:
                    recent_context = prev_msgs[-1].get("content", "")

        # 정책은 프로필 포함, 의학/감정은 의학 키워드 중심
        if intent == "policy":
            augmented = self.query_augmenter.augment(preprocessed, profile)
        else:
            augmented = self.query_augmenter.augment_medical(preprocessed, profile, recent_context=recent_context)

        # 멀티 쿼리 파싱 (줄바꿈 구분)
        queries = [q.strip().lstrip("-•→").strip() for q in augmented.split("\n") if q.strip()]
        if not queries:
            queries = [preprocessed]

        print(f"  [CareAgent:augment_query] {len(queries)}개 쿼리: {queries[:2]}")
        return {"search_queries": queries}

    def _retrieve(self, state: CareAgentState) -> dict:
        """벡터 검색: 멀티 쿼리 검색 후 중복 제거"""
        self._emit(state, "의학 자료를 찾아보고 있어요...")
        profile = state["profile"]
        intent = state["intent"]
        queries = state["search_queries"]

        all_docs = []
        seen_ids = set()

        for query in queries:
            docs = self.retriever.search(
                query=query,
                intent=intent,
                profile=profile,
            )
            for doc in docs:
                # 중복 제거 (content 앞 100자로 판별)
                doc_id = doc.content[:100]
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_docs.append(doc)

        print(f"  [CareAgent:retrieve] {len(all_docs)}건 (중복 제거 후)")
        return {"retrieved_docs": all_docs}

    def _rerank(self, state: CareAgentState) -> dict:
        """리랭킹"""
        self._emit(state, "비슷한 증상 사례를 분석하고 있어요...")
        profile = state["profile"]
        queries = state["search_queries"]
        docs = state["retrieved_docs"]

        if not docs:
            return {"reranked_docs": []}

        # 첫 번째 쿼리(원본에 가장 가까운)로 리랭킹
        primary_query = queries[0] if queries else state["preprocessed"]

        reranked = self.reranker.rerank(
            query=primary_query,
            user_context=profile.context_summary() if hasattr(profile, 'context_summary') else "",
            documents=docs,
        )

        print(f"  [CareAgent:rerank] {len(docs)} → {len(reranked)}건")
        for i, doc in enumerate(reranked):
            q = doc.metadata.get('question', '')[:60]
            print(f"    [{i+1}] {doc.collection} | {q or doc.content[:60]}...")
            print(f"         content: {doc.content[:200]}")
        return {"reranked_docs": reranked}

    def _kg_enrich(self, state: CareAgentState) -> dict:
        """KG 보강 + 정보갭 탐지"""
        profile = state["profile"]
        intent = state["intent"]
        reranked_docs = state["reranked_docs"]
        preprocessed = state["preprocessed"]

        kg_context = self.knowledge_enricher.enrich(
            documents=reranked_docs,
            profile=profile,
            intent=intent,
            user_message=preprocessed,
        )

        # 정보 갭 탐지
        all_entity_ids = set()
        for doc in reranked_docs:
            all_entity_ids.update(doc.entity_ids)

        info_gap_hint = self.info_gap_detector.detect(
            entity_ids=all_entity_ids,
            profile=profile,
            intent=intent,
            user_input=preprocessed,
        )

        print(f"  [CareAgent:kg_enrich] KG {len(kg_context)}자, gap={bool(info_gap_hint)}")
        return {"kg_context": kg_context, "info_gap_hint": info_gap_hint or ""}

    def _generate_response(self, state: CareAgentState) -> dict:
        """응답 생성"""
        self._emit(state, "답변을 준비하고 있어요...")
        profile = state["profile"]
        session = state["session"]
        intent_str = state["intent"]
        weight = state["weight"]
        reranked_docs = state.get("reranked_docs", [])
        kg_context = state.get("kg_context", "")
        info_gap_hint = state.get("info_gap_hint", "")

        # Intent 열거형 변환
        try:
            intent = Intent(intent_str)
        except ValueError:
            intent = Intent.MEDICAL

        # Tool 실행 (drug_search, hospital_search)
        session = state.get("session")
        history = session.get_recent_history(n=4) if session else []
        tool_context, tool_sources = self._run_tools(state["preprocessed"], profile, history=history)
        if tool_context:
            kg_context = f"{tool_context}\n\n{kg_context}"

        # Weight 열거형 변환
        try:
            weight_enum = Weight(weight)
        except ValueError:
            weight_enum = Weight.HEAVY

        response_text, profile_updates = self.response_generator.generate(
            user_input=state["preprocessed"],
            intent=intent,
            profile=profile,
            reranked_docs=reranked_docs,
            kg_context=kg_context,
            session=session,
            info_gap_hint=info_gap_hint if info_gap_hint else None,
            weight=weight_enum,
        )

        # 대화 턴 수 계산 (사용자 메시지 기준)
        session_history = state["session"].get_recent_history(n=20) if state.get("session") else []
        conversation_turns = len([m for m in session_history if m.get("role") == "user"])

        # YouTube 링크 카드 노출 조건: 2턴 이상 + score >= 0.55
        YOUTUBE_LINK_SCORE_THRESHOLD = 0.45
        MAX_YOUTUBE_LINKS = 4
        show_youtube_links = conversation_turns >= 1  # 이전 턴이 1개 이상 = 2번째 턴부터

        # links 추출: youtube/blog/web_reference URL 수집
        links = []
        youtube_link_count = 0
        # [DEBUG] blog 문서 payload 구조 확인
        blog_docs = [d for d in reranked_docs if d.collection == "blog"]
        if blog_docs:
            print(f"  [DEBUG:blog] {len(blog_docs)}건 reranked. 첫 번째 payload keys: {list(blog_docs[0].metadata.keys())}")
            print(f"  [DEBUG:blog] url={blog_docs[0].metadata.get('url')!r}, source={blog_docs[0].metadata.get('source')!r}, score={blog_docs[0].score:.3f}")
        else:
            print(f"  [DEBUG:blog] reranked_docs에 blog 없음 (전체 {len(reranked_docs)}건)")
        for doc in reranked_docs:
            url = doc.metadata.get("url") or ""
            # video_id: metadata에 직접 있거나, source 필드에서 "youtube:VIDEO_ID" 형식으로 파싱
            video_id = doc.metadata.get("video_id") or ""
            if not video_id and doc.collection == "youtube_qna":
                source_str = doc.metadata.get("source", "") or (doc.source if hasattr(doc, 'source') else "")
                if source_str.startswith("youtube:"):
                    video_id = source_str.split("youtube:", 1)[1].strip()
            if doc.collection == "youtube_qna" and video_id:
                # 링크 카드는 조건 충족 시만 (출처 텍스트는 별도로 항상 표시)
                if show_youtube_links and doc.score >= YOUTUBE_LINK_SCORE_THRESHOLD and youtube_link_count < MAX_YOUTUBE_LINKS:
                    title = doc.metadata.get("title") or doc.metadata.get("question", "전문가 영상")
                    if len(title) > 50:
                        title = title[:47] + "..."
                    links.append({
                        "url": f"https://youtu.be/{video_id}",
                        "title": title,
                        "channel": doc.metadata.get("channel", "전문 의료진 YouTube"),
                        "source_type": "youtube",
                        "video_id": video_id,
                    })
                    youtube_link_count += 1
            elif doc.collection == "blog" and url:
                links.append({
                    "url": url,
                    "title": doc.metadata.get("title", "경험담")[:50],
                    "source_type": "blog",
                })
            elif doc.collection == "web_reference" and url:
                links.append({
                    "url": url,
                    "title": doc.metadata.get("source", "참고자료"),
                    "source_type": "web_reference",
                })

        # 중복 URL 제거
        seen_urls = set()
        unique_links = []
        for link in links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                unique_links.append(link)

        # sources 수집 (blog는 카드로만 표시하므로 텍스트 출처에서 제외)
        text_sources = []
        for doc in reranked_docs:
            if not hasattr(doc, 'source') or not doc.source:
                continue
            if doc.collection == "blog":
                continue  # blog는 링크 카드로 표시하므로 텍스트 출처에서 제외
            if doc.collection == "youtube_qna":
                text_sources.append("전문 의료진 YouTube")
            else:
                text_sources.append(doc.source)
        sources_used = list(set(text_sources))
        sources_used.extend(tool_sources)

        # light 경로: 인메모리 데이터(KG/타임라인/트리플)는 PDF와 같은 출처
        if not sources_used and kg_context and kg_context.strip() != "(추가 정보 없음)":
            sources_used.append("건강보험심사평가원, 대한산부인과학회 보조생식술위원회")

        print(f"  [CareAgent:generate_response] 응답 {len(response_text)}자, links {len(unique_links)}개, sources {len(sources_used)}개")
        return {
            "response_text": response_text,
            "links": unique_links,
            "doctor_questions": [],
            "profile_updates": profile_updates,
            "sources_used": sources_used,
        }

    def _safety_check(self, state: CareAgentState) -> dict:
        """안전 필터"""
        response_text = state["response_text"]
        intent = state["intent"]

        safety = self.safety_filter.check_response(response_text, intent)
        flags = safety.get("flags", [])

        if flags:
            print(f"  [CareAgent:safety_check] 경고: {flags}")

        return {"safety_flags": flags}

    def _extract_doctor_questions(self, state: CareAgentState) -> dict:
        """응답에서 '다음 진료 때 물어볼 질문'을 LLM light로 추출 (safety_check과 병렬)"""
        response_text = state["response_text"]

        # 진료 관련 키워드가 없으면 스킵 (불필요한 LLM 호출 방지)
        trigger_keywords = ["진료", "선생님", "여쭤", "확인해", "물어보", "상의", "주치의", "상담", "담당"]
        if not any(kw in response_text for kw in trigger_keywords):
            return {"doctor_questions": []}

        user_input = state.get("preprocessed", "")
        prompt = f"""아래 대화에서, 사용자가 다음 진료 때 의사에게 꼭 확인해야 할 구체적 항목만 추출하세요.

## 사용자 질문
{user_input}

## AI 응답
{response_text}

## 추출 기준 — 이것만 추출
- 대화 중 나온 증상/구체적 수치/상태에 대한 의사 판단이 필요한 경우 (예: 과배란 5일째 복통 → "과배란 주사 5일째 복통 증상 확인")
- AI가 답변 중 "다음 진료 때 ~여쭤보세요"라고 구체적으로 안내한 항목

## 추출하면 안 되는 것 (반드시 제외)
- 사용자가 당연히 스스로 물어볼 것 (검사 결과 확인, 다음 일정 확인, 최선의 방법 상의)
- AI가 이미 충분히 답변한 일반 정보
- "관계 개선 방법", "스트레스 관리" 같은 비의학적 항목
- 구체적 맥락 없이 뭉뚱그린 표현 ("종합적인 판단 여쭤보기", "최선의 방법 여쭤보기")

## 말투: 구체적 상황 + 확인 행동 (짧게)
✅ "과배란 주사 5일째 복통 — 정상 범위인지 확인"
✅ "이식 후 출혈 지속 시 병원 연락 필요"
✅ "난자 질 개선 영양제(코큐텐 등) 복용해도 되는지 확인"
❌ "검사 결과에 대해 여쭤보기"
❌ "현재 상태에 맞는 최선의 방법 상의하기"

## 출력 형식 (JSON 리스트만, 없으면 빈 리스트)
["질문1"]"""

        try:
            result = self.llm_light.invoke(prompt)
            text = result.content.strip()

            # ```json ... ``` 래핑 제거
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
                print(f"  [CareAgent:extract_doctor_questions] {len(questions)}개 추출: {questions}")
            else:
                print("  [CareAgent:extract_doctor_questions] 추출 없음")

            return {"doctor_questions": questions}

        except Exception as e:
            print(f"  [CareAgent:extract_doctor_questions] 파싱 실패: {e}")
            return {"doctor_questions": []}

    def _generate_suggestions(self, state: CareAgentState) -> dict:
        """medical-heavy일 때만 사용자 예시 답변 3개 생성 (gpt-4o-mini)"""
        if state["intent"] != "medical" or state["weight"] != "heavy":
            return {"suggested_replies": []}

        # 이미 2턴 이상 대화 중이면 suggestion 루프 방지
        messages = state.get("messages", [])
        user_turn_count = sum(1 for m in messages if m.get("role") == "user")
        if user_turn_count >= 3:
            return {"suggested_replies": []}

        response_text = state["response_text"]

        # 이전 대화에서 사용자가 이미 답한 내용 정리
        prior_user_msgs = [m["content"] for m in messages if m.get("role") == "user"]
        prior_context = "\n".join(f"- {c}" for c in prior_user_msgs) if prior_user_msgs else ""

        prompt = f"""아래는 난임 시술 AI 라일의 응답입니다. 사용자가 이 응답을 받고 보낼 수 있는 짧은 답변 예시 3개를 생성하세요.

## 이전 대화에서 사용자가 이미 말한 내용
{prior_context if prior_context else "(없음)"}

## AI 응답 (현재 질문)
{response_text}

## 규칙
1. 응답에 질문이 있을 때만 생성. 질문이 없으면 아무것도 출력하지 않음.
2. 사용자 입장에서 자연스러운 구어체 한국어
3. 각 항목은 20자 이내로 간결하게
4. **이미 말한 내용과 겹치는 답변 금지** — 사용자가 이미 답한 증상/상황을 다시 제안하지 말 것
5. AI가 묻는 질문에 맞는 답변 예시를 생성 (증상 묻는 중이면 증상, 기간 묻는 중이면 기간 등)
6. 서로 다른 상황을 반영한 3가지 옵션
7. 번호나 기호 없이 텍스트만, 줄바꿈으로 구분

출력:"""

        try:
            result = self.llm_light.invoke(prompt)
            lines = [l.strip() for l in result.content.strip().split("\n") if l.strip()]
            suggestions = lines[:3]
            print(f"  [CareAgent:generate_suggestions] {len(suggestions)}개: {suggestions}")
            return {"suggested_replies": suggestions}
        except Exception as e:
            print(f"  [CareAgent:generate_suggestions] 오류: {e}")
            return {"suggested_replies": []}

    # ─── Tool 실행 ───────────────────────────────────────

    def _run_tools(self, message: str, profile: UserProfile, history: list[dict] = None) -> tuple:
        """drug_search, hospital_search tool 실행"""
        if not self.tool_router:
            return "", []

        needed_tools = self.tool_router.route(message, history=history)
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

    def _run_drug_search(self, message: str):
        import re
        drug_patterns = [
            "세트로타이드", "세트로렐릭스", "가니레릭스", "가니레버",
            "고나도트로핀", "폴리트롭", "퓨레곤", "메노퓨어",
            "클로미펜", "클로미드", "레트로졸", "페마라",
            "프로게스테론", "유트로게스탄", "듀파스톤", "크리논",
            "오비드렐", "프레그닐", "루프론", "데카펩틸",
            "메트포르민", "에스트라디올", "프레마린", "프로기노바",
            "아스피린", "헤파린", "클렉산",
        ]
        found = [d for d in drug_patterns if d in message]
        if not found:
            matches = re.findall(r'([가-힣]{2,8}(?:주사|주|약|정|캡슐|젤))', message)
            found = matches[:1]
        if not found:
            return None
        result = self.drug_search.search(found[0])
        if not result["found"]:
            return None
        context = f"[약물 정보 — {found[0]}]\n출처: {result['source']}\n"
        if result.get("summary"):
            context += f"요약: {result['summary']}\n"
        return {"context": context, "source": result["source"]}

    def _run_hospital_search(self, message: str, profile: UserProfile):
        treatment_type = ""
        if any(kw in message for kw in ["체외수정", "시험관", "IVF", "ivf"]):
            treatment_type = "ivf"
        elif any(kw in message for kw in ["인공수정", "IUI", "iui"]):
            treatment_type = "iui"
        region = profile.region or ""
        result = self.hospital_search.search(region=region, treatment_type=treatment_type, include_nearby=True)
        if not result["found"]:
            return None
        lines = [f"[난임 지정병원 — {region or '전국'}]"]
        for h in result.get("hospitals", []):
            lines.append(f"  - {h['병원명']} ({h['종별']}) | ☎ {h['전화번호']}{' | 🌐 ' + h['홈페이지'] if h.get('홈페이지') else ''}")
        for h in result.get("nearby_hospitals", []):
            lines.append(f"  - {h['병원명']} ({h.get('시군구', '')}) | ☎ {h['전화번호']}")
        return {"context": "\n".join(lines), "source": "HIRA 난임 지정병원 데이터"}

    # ─── 메인 진입점 ─────────────────────────────────────

    def run(
        self,
        preprocessed: str,
        intent: Intent,
        profile: UserProfile,
        session: ChatSession,
        weight: str = "",
        status_callback=None,
    ) -> dict:
        """CareAgent 실행 — Supervisor에서 호출 (weight는 Supervisor가 전달)"""
        initial_state = {
            "preprocessed": preprocessed,
            "intent": intent.value if hasattr(intent, "value") else intent,
            "profile": profile,
            "messages": session.get_recent_history(10),
            "session": session,
            "weight": weight,
            "search_queries": [],
            "retrieved_docs": [],
            "reranked_docs": [],
            "inmemory_context": "",
            "kg_context": "",
            "info_gap_hint": "",
            "response_text": "",
            "links": [],
            "doctor_questions": [],
            "safety_flags": [],
            "profile_updates": {},
            "sources_used": [],
            "suggested_replies": [],
            "status_callback": status_callback,
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
            "suggested_replies": result.get("suggested_replies", []),
        }
