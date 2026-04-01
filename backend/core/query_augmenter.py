"""
[Step 3] 쿼리 증강
검색 쿼리를 최적화합니다.

- 상담용(counseling): 핵심 의학 키워드만 증강 (프로필 노이즈 제거)
- 정보용(info): 프로필 정보 포함 (지원금은 지역/나이/혼인 등에 따라 다르므로)
"""
from prompts.templates import QUERY_AUGMENTATION, QUERY_AUGMENTATION_MEDICAL
from prompts import get_templates
from core.llm_client import LLMClient
from models import UserProfile


class QueryAugmenter:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def augment(self, user_input: str, profile: UserProfile) -> str:
        """
        정보 에이전트용: 프로필 정보를 포함한 검색 쿼리 생성.
        지원금/정책 검색에서는 지역, 나이, 혼인 상태 등이 중요합니다.
        """
        prompt = QUERY_AUGMENTATION.format(
            user_context=profile.context_summary(),
            user_input=user_input,
        )

        augmented = self.llm.generate_light(prompt, max_tokens=100)
        augmented = augmented.strip().strip('"').strip("'")

        if not augmented or len(augmented) < len(user_input):
            augmented = self._fallback_augment(user_input, profile)

        return augmented

    def augment_medical(self, user_input: str, profile: UserProfile, recent_context: str = "") -> str:
        """
        상담 에이전트용: 핵심 의학 키워드만 증강.
        나이, 지역, 진단명 등 프로필 정보는 벡터 검색 노이즈가 되므로 제외.
        시술 단계와 의학 용어 확장만 수행합니다.
        """
        # 후속 질문인 경우 대화 맥락을 질문에 포함
        effective_input = user_input
        if recent_context:
            effective_input = f"[이전 대화 맥락: {recent_context}]\n현재 질문: {user_input}"

        mode = getattr(profile, 'mode', 'medical')
        t = get_templates(mode)
        prompt = t.QUERY_AUGMENTATION_MEDICAL.format(
            treatment_stage=profile.treatment_stage or "",
            protocol=profile.protocol or "",
            current_phase=profile.current_phase or "",
            user_input=effective_input,
        )

        augmented = self.llm.generate_light(prompt, max_tokens=100)
        augmented = augmented.strip().strip('"').strip("'")

        if not augmented or len(augmented) < len(user_input):
            augmented = self._fallback_medical(user_input, profile)

        return augmented

    def _fallback_augment(self, user_input: str, profile: UserProfile) -> str:
        """정보용 폴백: 프로필 정보 포함"""
        parts = [user_input]

        if profile.treatment_stage:
            parts.append(profile.treatment_stage)
        if profile.protocol:
            parts.append(profile.protocol)
        if profile.current_phase:
            parts.append(profile.current_phase)
        if profile.treatment_cycle > 0:
            parts.append(f"{profile.treatment_cycle}회차")
        if profile.age:
            parts.append(f"{profile.age}세")
        if profile.region:
            parts.append(profile.region)

        return " ".join(parts)

    # 다른 시술 단계를 언급하는 키워드
    _OTHER_STAGE_KEYWORDS = [
        "시험관", "체외수정", "IVF", "ivf",
        "인공수정", "IUI", "iui",
        "배아 이식", "이식", "채란", "난자 채취",
        "동결배아", "FET", "해동",
        "배란 유도", "타이밍",
    ]

    def _fallback_medical(self, user_input: str, profile: UserProfile) -> str:
        """상담용 폴백: 질문이 다른 시술에 대한 것이면 현재 단계를 붙이지 않음"""
        parts = [user_input]

        # 질문이 사용자의 현재 단계가 아닌 다른 시술을 언급하면 단계 키워드 생략
        if profile.treatment_stage and not self._mentions_other_stage(user_input, profile.treatment_stage):
            parts.append(profile.treatment_stage)
        if profile.protocol:
            parts.append(profile.protocol)
        if profile.current_phase:
            parts.append(profile.current_phase)

        return " ".join(parts)

    def _mentions_other_stage(self, user_input: str, current_stage: str) -> bool:
        """질문이 현재 단계와 다른 시술을 언급하는지 확인"""
        input_lower = user_input.lower()
        current_lower = current_stage.lower() if current_stage else ""

        for kw in self._OTHER_STAGE_KEYWORDS:
            if kw.lower() in input_lower and kw.lower() not in current_lower:
                return True
        return False
