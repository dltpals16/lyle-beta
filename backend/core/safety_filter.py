"""
[Step 8] 안전 필터
AI 응답의 안전성을 검증합니다.
- 의료적 확언 체크
- 위기 상황 감지
- 면책 포함 확인
"""
from config import CRISIS_KEYWORDS
from prompts.templates import SAFETY_FILTER
from core.llm_client import LLMClient


class SafetyFilter:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    # ── 위기 감지 (사용자 입력 체크) ──

    def check_crisis(self, user_input: str) -> dict:
        """
        사용자 입력에서 위기 상황을 감지합니다.
        Returns: {"is_crisis": bool, "keywords_found": list}
        """
        found = []
        for kw in CRISIS_KEYWORDS:
            if kw in user_input:
                found.append(kw)

        return {
            "is_crisis": len(found) > 0,
            "keywords_found": found,
        }

    # ── 응답 안전성 체크 ──

    def check_response(self, response: str, intent: str) -> dict:
        """
        AI 응답의 안전성을 룰 기반으로 체크합니다.
        Returns: {"is_safe": bool, "flags": list, "corrected": str | None}
        """
        flags = []
        corrected = response

        # 1. 확정적 의료 진단 표현 체크
        diagnosis_patterns = [
            "입니다.", "확실합니다", "틀림없", "분명히",
            "100%", "반드시 그래요", "정상입니다", "비정상입니다",
        ]
        for pattern in diagnosis_patterns:
            if pattern in response:
                flags.append(f"확정 표현 감지: '{pattern}'")

        # 2. 약물 변경 권유 체크
        med_change_patterns = [
            "약을 바꾸", "용량을 조절", "약을 중단", "주사를 멈추",
            "복용을 중지", "약을 늘려", "약을 줄여",
        ]
        for pattern in med_change_patterns:
            if pattern in response:
                flags.append(f"약물 변경 권유 감지: '{pattern}'")

        # 3. 면책 문구 확인 (의학 관련 답변인 경우)
        if intent == "medical":
            disclaimer_keywords = [
                "선생님", "진료", "상담", "확인", "병원",
                "담당", "의사", "전문가",
            ]
            has_disclaimer = any(kw in response for kw in disclaimer_keywords)
            if not has_disclaimer:
                flags.append("면책 문구 누락 (증상 답변)")

        is_safe = len(flags) == 0

        return {
            "is_safe": is_safe,
            "flags": flags,
            "corrected": None if is_safe else corrected,
        }

    def get_crisis_response(self) -> str:
        """위기 상황 감지 시 제공할 응답"""
        return (
            "지금 많이 힘드시죠. 그 마음이 충분히 이해돼요.\n\n"
            "혼자 감당하기 어려운 마음이 드신다면, "
            "전문 상담을 받아보시는 것도 방법이에요.\n\n"
            "📞 정신건강 위기상담 1577-0199 (24시간)\n"
            "📞 자살예방 상담전화 1393 (24시간)\n\n"
            "언제든 이야기하고 싶을 때, 저는 여기 있을게요 💜"
        )

    # ── LLM 기반 심층 체크 (선택적) ──

    def deep_check(self, response: str) -> dict:
        """
        LLM으로 응답 안전성을 심층 검증합니다.
        비용이 들므로 룰 기반에서 의심되는 경우에만 호출.
        """
        prompt = SAFETY_FILTER.format(response=response)
        result = self.llm.generate_light(prompt, max_tokens=100)

        if result.strip().startswith("PASS"):
            return {"is_safe": True, "flags": [], "corrected": None}
        else:
            parts = result.split("|")
            return {
                "is_safe": False,
                "flags": [parts[1].strip() if len(parts) > 1 else "LLM 검증 실패"],
                "suggestion": parts[2].strip() if len(parts) > 2 else None,
            }
