"""
RecommendAgent — 헬스케어 제품 추천 (LangGraph 서브그래프)

지원 카테고리:
- 영양제 (엽산, 비타민, 오메가-3 등)
- 진단/계측 기기 (배란/임신 테스트기, 체온계 등)
- 운동/스트레칭 (폼롤러, 마사지볼, 요가매트)
- 이완/마사지 (족욕기, 안마기, 반신욕 용품)
- 건강식품 (콜라겐, 단백질, 즙류 등)

그래프 구조:
  classify_category → analyze_user → decide_products → enrich_drug (옵션) →
  search_shopping → generate_response → END
"""
import json
import os
from typing import TypedDict, Any, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from config import OPENAI_MODEL_MAIN, OPENAI_MODEL_LIGHT
from models import UserProfile, ChatSession
from core.tools.shopping_search import ShoppingSearchTool, Product
from core.tools.drug_search import DrugSearchTool


# ─────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────

class RecommendAgentState(TypedDict):
    preprocessed: str
    profile: Any
    session: Any
    messages: list

    # 분석 결과
    category: str                       # 영양제/진단기기/운동도구/이완용품/건강식품
    user_situation: dict                # {"goal": "임신준비", "concerns": [...], ...}
    target_products: list               # ["활성형 엽산", "비타민 D"]
    drug_info: str                      # 영양제일 때만 채워짐

    # 검색 결과
    shopping_results: list              # list[dict] (Product → dict 직렬화)

    # 응답
    response_text: str
    links: list
    safety_flags: list
    profile_updates: dict
    sources_used: list


CATEGORIES = ["영양제", "진단기기", "운동도구", "이완용품", "건강식품"]
CATEGORIES_NEEDING_DRUG_INFO = {"영양제", "건강식품"}


# ─────────────────────────────────────────────────────────────────────
# 프롬프트
# ─────────────────────────────────────────────────────────────────────

CLASSIFY_CATEGORY_PROMPT = """사용자의 추천 요청을 다음 카테고리 중 하나로 분류하세요.

## 카테고리
- 영양제: 비타민, 미네랄, 엽산, 오메가-3, 유산균 등 먹는 영양 보충제
- 진단기기: 배란/임신 테스트기, 체온계, 혈압계, 혈당계 등 측정 기기
- 운동도구: 폼롤러, 마사지볼, 요가매트, 풀업밴드, 짐볼 등 운동/스트레칭 용품
- 이완용품: 족욕기, 안마기, 반신욕 보조용품, 마사지 의자 등 휴식/이완 도구
- 건강식품: 콜라겐, 단백질 분말, 즙류, 차, 환 등 식품 형태 건강 보조

## 사용자 발화
{user_input}

## 사용자 정보 (참고)
{user_context}

위 발화의 카테고리만 한 단어로 출력 (영양제/진단기기/운동도구/이완용품/건강식품 중 하나)."""


ANALYZE_USER_PROMPT = """사용자의 발화와 프로필을 분석해 추천에 필요한 상황을 추출하세요.

## 카테고리
{category}

## 사용자 발화
{user_input}

## 사용자 정보
{user_context}

## 최근 대화
{recent_messages}

JSON으로 답하세요 (한 줄):
{{
  "goal": "사용자가 원하는 목적 (예: 임신준비, 피로개선, 면역강화)",
  "concerns": ["고민/증상 키워드 리스트"],
  "constraints": ["제약사항 (예: 비건, 임산부, 알레르기)"],
  "context_note": "추가 컨텍스트 한 줄"
}}"""


DECIDE_PRODUCTS_PROMPT = """사용자 상황에 맞는 추천 제품 종류를 결정하세요.

## 카테고리
{category}

## 사용자 상황
{user_situation}

## 작업
이 사용자에게 적합한 제품 종류 2~4개를 선택하세요.
- 영양제/건강식품: 구체적 성분명 (예: "활성형 엽산", "비타민 D3", "마그네슘 비스글리시네이트")
- 진단기기: 종류명 (예: "디지털 배란 테스트기", "비접촉 적외선 체온계")
- 운동도구: 종류 + 부위 (예: "어깨 마사지볼", "요가용 폼롤러")
- 이완용품: 종류 + 용도 (예: "발 마사지 족욕기")

JSON 배열로 답하세요 (한 줄):
["제품종류1", "제품종류2", ...]"""


GENERATE_RESPONSE_PROMPT = """당신은 라일의 헬스케어 추천 어드바이저입니다.
사용자 상황에 맞춰 추천 이유를 친절하고 전문적으로 설명하고, 검증된 쇼핑몰 상품을 안내하세요.

## 톤
- 따뜻하지만 전문적
- 추천 이유를 명확히 설명 (왜 이 성분/기기/도구가 맞는지)
- 단정하지 말고 권장 형태로 ("~이 좋아요", "~을 추천드려요")

## 카테고리
{category}

## 사용자 상황
{user_situation}

## 추천할 제품 종류
{target_products}

## (영양제일 때) 약학정보원에서 가져온 정보
{drug_info}

## 검증된 쇼핑몰 검색 결과
{shopping_summary}

## 답변 작성 규칙
1. 첫 줄: 사용자 상황 공감 + 추천 요지 (1-2줄)
2. 추천 이유 설명 (성분/기능의 특징과 사용자에게 맞는 이유)
3. 상품 카드는 따로 표시되므로 답변 본문에 URL/가격 직접 적지 말 것
4. 마지막: 안전 안내 (한 줄)
   - 영양제/건강식품: "복약 중이거나 임신/수유 중이시면 의사·약사 상담 후 복용하시는 게 안전해요."
   - 진단기기: "정확한 결과는 의료기관 검사로 확인해 주세요."
   - 운동도구/이완용품: "통증이나 부상이 있으시면 무리하지 마세요."

답변(자연어 텍스트, 마크다운 가능):"""


# ─────────────────────────────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────────────────────────────

class RecommendAgent:
    """헬스케어 제품 추천 에이전트 (LangGraph 서브그래프)"""

    def __init__(
        self,
        shopping_search: ShoppingSearchTool,
        drug_search: Optional[DrugSearchTool] = None,
    ):
        self.shopping_search = shopping_search
        self.drug_search = drug_search

        self.llm_main = ChatOpenAI(
            model=OPENAI_MODEL_MAIN,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,
        )
        self.llm_light = ChatOpenAI(
            model=OPENAI_MODEL_LIGHT,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0,
        )

        self.graph = self._build_graph()
        print("[RecommendAgent] LangGraph 초기화 완료")

    # ── 그래프 빌드 ──

    def _build_graph(self):
        wf = StateGraph(RecommendAgentState)

        wf.add_node("classify_category", self._classify_category)
        wf.add_node("analyze_user", self._analyze_user)
        wf.add_node("decide_products", self._decide_products)
        wf.add_node("enrich_drug_info", self._enrich_drug_info)
        wf.add_node("search_shopping", self._search_shopping)
        wf.add_node("generate_response", self._generate_response)

        wf.set_entry_point("classify_category")
        wf.add_edge("classify_category", "analyze_user")
        wf.add_edge("analyze_user", "decide_products")

        # 영양제/건강식품만 약학정보원 보강
        wf.add_conditional_edges(
            "decide_products",
            self._route_after_decide,
            {
                "drug": "enrich_drug_info",
                "no_drug": "search_shopping",
            },
        )
        wf.add_edge("enrich_drug_info", "search_shopping")
        wf.add_edge("search_shopping", "generate_response")
        wf.add_edge("generate_response", END)

        return wf.compile()

    # ── 노드들 ──

    def _classify_category(self, state: RecommendAgentState) -> dict:
        prompt = CLASSIFY_CATEGORY_PROMPT.format(
            user_input=state["preprocessed"],
            user_context=_safe_context(state.get("profile")),
        )
        resp = self.llm_light.invoke(prompt).content.strip()
        cat = next((c for c in CATEGORIES if c in resp), "영양제")
        print(f"[RecommendAgent] 카테고리: {cat}")
        return {"category": cat}

    def _analyze_user(self, state: RecommendAgentState) -> dict:
        session = state.get("session")
        recent = ""
        if session is not None:
            try:
                history = session.get_recent_history(4)
                recent = "\n".join(
                    f"[{m['role']}] {m['content'][:100]}" for m in history
                )
            except Exception:
                recent = ""

        prompt = ANALYZE_USER_PROMPT.format(
            category=state["category"],
            user_input=state["preprocessed"],
            user_context=_safe_context(state.get("profile")),
            recent_messages=recent or "(없음)",
        )
        raw = self.llm_light.invoke(prompt).content
        situation = _parse_json_safe(raw, default={"goal": "", "concerns": [], "constraints": [], "context_note": ""})
        print(f"[RecommendAgent] 사용자 상황: {situation}")
        return {"user_situation": situation}

    def _decide_products(self, state: RecommendAgentState) -> dict:
        prompt = DECIDE_PRODUCTS_PROMPT.format(
            category=state["category"],
            user_situation=json.dumps(state["user_situation"], ensure_ascii=False),
        )
        raw = self.llm_main.invoke(prompt).content
        products = _parse_json_safe(raw, default=[])
        if not isinstance(products, list):
            products = []
        # 최대 4개
        products = [p for p in products if isinstance(p, str)][:4]
        print(f"[RecommendAgent] 추천 종류: {products}")
        return {"target_products": products}

    def _route_after_decide(self, state: RecommendAgentState) -> str:
        if state["category"] in CATEGORIES_NEEDING_DRUG_INFO and self.drug_search:
            return "drug"
        return "no_drug"

    def _enrich_drug_info(self, state: RecommendAgentState) -> dict:
        """영양제/건강식품에 한해 약학정보원에서 정보 보강 (선택적, 실패해도 진행)."""
        if not self.drug_search:
            return {"drug_info": ""}

        infos = []
        for product_name in state["target_products"][:2]:  # 비용 절약: 최대 2개만
            try:
                r = self.drug_search.search(product_name)
                if r.get("found") and r.get("detail"):
                    infos.append(f"[{product_name}]\n{r['detail'][:600]}")
            except Exception as e:
                print(f"  [RecommendAgent] drug_search 실패 ({product_name}): {e}")

        joined = "\n\n".join(infos)
        return {"drug_info": joined}

    def _search_shopping(self, state: RecommendAgentState) -> dict:
        """추천할 제품 종류마다 네이버 쇼핑 검색 후 통합."""
        all_results: list[Product] = []
        per_product = max(2, 6 // max(len(state["target_products"]), 1))
        for query in state["target_products"]:
            try:
                ps = self.shopping_search.search(
                    query=query,
                    max_results=per_product + 2,
                )
                # 검색 키워드를 제품과 매칭하기 위해 title에 키워드 포함 우선
                ps = sorted(ps, key=lambda p: 0 if any(w in p.title for w in query.split()) else 1)
                all_results.extend(ps[:per_product])
            except Exception as e:
                print(f"  [RecommendAgent] shopping 검색 실패 ({query}): {e}")

        # 중복 제거 (product_id 기준)
        seen = set()
        deduped: list[Product] = []
        for p in all_results:
            if p.product_id and p.product_id not in seen:
                seen.add(p.product_id)
                deduped.append(p)

        print(f"[RecommendAgent] 쇼핑 결과: {len(deduped)}건")
        return {"shopping_results": [_product_to_dict(p) for p in deduped[:8]]}

    def _generate_response(self, state: RecommendAgentState) -> dict:
        shopping_summary = _format_shopping_summary(state.get("shopping_results", []))

        prompt = GENERATE_RESPONSE_PROMPT.format(
            category=state["category"],
            user_situation=json.dumps(state["user_situation"], ensure_ascii=False),
            target_products=", ".join(state["target_products"]) or "(미정)",
            drug_info=state.get("drug_info") or "(없음)",
            shopping_summary=shopping_summary,
        )
        text = self.llm_main.invoke(prompt).content.strip()

        # 링크 정리 (Supervisor가 직렬화)
        links = [
            {
                "title": p["title"],
                "url": p["link"],
                "price": p["price_display"],
                "mall": p["mall_name"],
                "image": p.get("image"),
            }
            for p in state.get("shopping_results", [])
        ]

        return {
            "response_text": text,
            "links": links,
            "safety_flags": [],
            "profile_updates": {},
            "sources_used": ["네이버쇼핑"] + (["약학정보원"] if state.get("drug_info") else []),
        }

    # ── 외부 인터페이스 ──

    def run(
        self,
        preprocessed: str,
        profile: UserProfile,
        session: ChatSession,
    ) -> dict:
        """Supervisor에서 호출."""
        initial: RecommendAgentState = {
            "preprocessed": preprocessed,
            "profile": profile,
            "session": session,
            "messages": session.get_recent_history(10) if session else [],
            "category": "",
            "user_situation": {},
            "target_products": [],
            "drug_info": "",
            "shopping_results": [],
            "response_text": "",
            "links": [],
            "safety_flags": [],
            "profile_updates": {},
            "sources_used": [],
        }
        final = self.graph.invoke(initial)
        return {
            "response": final.get("response_text", ""),
            "links": final.get("links", []),
            "doctor_questions": [],
            "safety_flags": final.get("safety_flags", []),
            "profile_updates": final.get("profile_updates", {}),
            "sources_used": final.get("sources_used", []),
            "reranked_docs": [],
            "kg_context": "",
            "suggested_replies": [],
        }


# ─────────────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────────────

def _safe_context(profile) -> str:
    if profile is None:
        return "(프로필 없음)"
    try:
        return profile.context_summary()
    except Exception:
        return "(프로필 요약 실패)"


def _parse_json_safe(raw: str, default):
    """LLM 응답에서 JSON 파싱. 실패 시 default."""
    import re
    s = raw.strip()
    # 코드 블록 제거
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    # JSON 추출
    m = re.search(r"(\[.*\]|\{.*\})", s, re.S)
    if m:
        s = m.group(1)
    try:
        return json.loads(s)
    except Exception:
        return default


def _product_to_dict(p: Product) -> dict:
    return {
        "title": p.title,
        "link": p.link,
        "image": p.image,
        "lprice": p.lprice,
        "price_display": p.display_price(),
        "mall_name": p.mall_name,
        "product_id": p.product_id,
        "category": p.category4 or p.category3 or p.category2 or "",
        "brand": p.brand,
    }


def _format_shopping_summary(items: list) -> str:
    if not items:
        return "(검색 결과 없음)"
    lines = []
    for i, p in enumerate(items[:6], 1):
        lines.append(
            f"{i}. [{p.get('mall_name','?')}] {p.get('title','')[:60]} "
            f"({p.get('price_display','?')}, 카테고리: {p.get('category','')})"
        )
    return "\n".join(lines)
