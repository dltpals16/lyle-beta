"""
[Step 2] 의도 분류
Few-shot 프롬프트로 사용자 의도와 경중을 동시에 분류합니다.
"""
from typing import Optional, Tuple
from config import Intent, Weight, CRISIS_KEYWORDS
from prompts.templates import INTENT_CLASSIFIER
from prompts import get_templates
from core.llm_client import LLMClient


class IntentClassifier:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.valid_intents = {e.value for e in Intent}
        self.valid_weights = {e.value for e in Weight}

    def classify(
        self,
        user_input: str,
        user_context: str,
        recent_messages: str = "",
        history: list[dict] = None,
        mode: str = "medical",
    ) -> Tuple[Intent, Optional[Weight]]:
        """
        사용자 메시지의 의도와 경중을 분류합니다.

        반환: (Intent, Optional[Weight])
        - out_of_scope: (Intent.OUT_OF_SCOPE, None)
        - 그 외: (Intent, Weight)

        1. 룰 기반 사전 체크 (위기 키워드)
        2. LLM 기반 분류 (intent|weight 형식)
        """
        # ── 룰 기반 사전 체크 ──
        lower_input = user_input.lower()

        # 위기 키워드 → emotion 우선 (안전 필터에서 추가 처리)
        for kw in CRISIS_KEYWORDS:
            if kw in lower_input:
                return (Intent.EMOTION, Weight.HEAVY)

        # ── LLM 기반 분류 ──
        t = get_templates(mode)
        prompt = t.INTENT_CLASSIFIER.format(
            user_context=user_context,
            recent_messages=recent_messages or "(첫 대화)",
            user_input=user_input,
        )

        response = self.llm.generate(
            system_prompt="당신은 난임 챗봇의 의도 분류기입니다. intent|weight 형식으로만 응답하세요.",
            user_message=prompt,
            max_tokens=20,
            history=history,
        )
        raw = response.strip().lower()

        # "intent|weight" 형식 파싱
        parts = raw.split("|")
        intent_str = parts[0].strip()

        # intent 부분 매칭 시도
        if intent_str not in self.valid_intents:
            for valid in self.valid_intents:
                if valid in intent_str:
                    intent_str = valid
                    break
            else:
                # 매칭 실패 → 기본값
                return (Intent.MEDICAL, Weight.HEAVY)

        intent = Intent(intent_str)

        # out_of_scope는 weight 없이 반환
        if intent == Intent.OUT_OF_SCOPE:
            return (Intent.OUT_OF_SCOPE, None)

        # weight 추출
        weight = Weight.HEAVY  # 기본값
        if len(parts) > 1:
            weight_str = parts[1].strip()
            if weight_str in self.valid_weights:
                weight = Weight(weight_str)

        return (intent, weight)
