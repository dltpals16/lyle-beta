"""
Tool 라우터 — 사용자 메시지를 보고 어떤 tool이 필요한지 판단
gpt-4o-mini로 경량 판단
"""
from core.llm_client import LLMClient


ROUTER_PROMPT = """사용자 메시지를 보고, 아래 도구 중 필요한 것을 판단하세요.

## 사용 가능한 도구
- drug_search: 약물/주사제 상세 정보가 필요할 때 (용법, 부작용, 성분, 급여 정보)
  예: "세트로타이드 부작용", "레트로졸 어떻게 먹어?", "고나도트로핀 주사 가격"
- hospital_search: 난임 병원을 찾을 때 (위치, 시술 가능 여부)
  예: "마포구 난임 병원", "체외수정 가능한 병원", "근처 난임센터"
- none: 도구 불필요 (일반 상담, 감정 지지, 시술 과정 질문 등)

## 판단 기준
- 특정 약물명이 언급되고 상세 정보를 원하면 → drug_search
- 병원 찾기/추천/위치를 원하면 → hospital_search
- 일반적인 "약 먹어야 하나요?" 같은 질문은 → none (벡터DB로 충분)
- 여러 도구가 필요하면 쉼표로 구분

## 사용자 메시지
{message}

필요한 도구(drug_search, hospital_search, none 중 선택):"""


class ToolRouter:
    """메시지 기반 tool 라우팅"""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        print("[ToolRouter] 초기화 완료")

    def route(self, message: str, history: list[dict] = None) -> list[str]:
        """
        메시지를 분석하여 필요한 tool 목록 반환.

        Returns:
            ["drug_search"], ["hospital_search"], ["drug_search", "hospital_search"], []
        """
        response = self.llm.generate_light(
            ROUTER_PROMPT.format(message=message),
            max_tokens=20,
            history=history,
        )
        response = response.strip().lower()

        tools = []
        if "drug_search" in response:
            tools.append("drug_search")
        if "hospital_search" in response:
            tools.append("hospital_search")

        print(f"  [ToolRouter] '{message[:30]}...' → {tools if tools else 'none'}")
        return tools
