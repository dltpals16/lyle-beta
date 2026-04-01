"""
라일(Lyle) 챗봇 — 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date, datetime
from enum import Enum


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"


class UserProfile(BaseModel):
    """사용자 프로필 (온보딩에서 수집)"""
    user_id: str
    name: str
    mode: str = "medical"                               # "medical" | "natural"
    birth_date: date
    gender: Gender
    last_period_date: Optional[date] = None        # 직전 생리 시작일
    treatment_stage: str = "준비 중"                # 시술 단계
    treatment_cycle: int = 0                        # 시술 회차 (0=준비 중)
    protocol: Optional[str] = None                  # 장기요법/단기요법/길항제/자연주기
    current_phase: Optional[str] = None             # 현재 세부 단계 (과배란 유도 중, 이식 후 D+7 등)
    embryo_grade: Optional[str] = None              # 배아 등급
    region: Optional[str] = None                    # 지역 (지원금 계산용)
    amh: Optional[float] = None                     # AMH 수치
    diagnoses: list[str] = []                       # 난임 원인 진단명 (pcos, dor, tubal 등)
    infertility_duration: Optional[str] = None      # 난임 기간 (under1, 1to2, 2to3 등)
    partner_linked: bool = False                    # 파트너 연동 여부
    # 추가 필드 (정책 안내 분기 + 맞춤 상담용)
    marriage_status: Optional[str] = None           # 혼인 상태: "legal" (법적혼인) / "defacto" (사실혼)
    dual_income: Optional[bool] = None              # 맞벌이 여부 (세액공제 전략 분기용)
    previous_treatments: list[dict] = []            # 이전 시술 이력 [{"type": "IVF", "cycle": 1, "result": "fail"}, ...]
    partner_diagnosis: Optional[str] = None         # 남성 측 진단 (male_factor, azoospermia 등)
    frozen_embryo_count: Optional[int] = None       # 보유 동결배아 수
    current_medications: list[str] = []             # 현재 복용 중인 약물
    notes: list[dict] = []                           # 채팅 기억 [{"id": "...", "content": "...", "created_at": "..."}]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def stage_id(self) -> str:
        """KG stage_id로 변환"""
        from config import STAGE_MAPPING
        return STAGE_MAPPING.get(self.treatment_stage, "S01")

    def context_summary(self) -> str:
        """LLM 프롬프트에 주입할 요약 문자열"""
        parts = [f"이름: {self.name}", f"나이: {self.age}세"]

        if self.treatment_stage:
            parts.append(f"시술 단계: {self.treatment_stage}")
        if self.treatment_cycle > 0:
            parts.append(f"시술 회차: {self.treatment_cycle}회차")
        if self.protocol:
            parts.append(f"프로토콜: {self.protocol}")
        if self.current_phase:
            parts.append(f"현재 상태: {self.current_phase}")
        if self.embryo_grade:
            parts.append(f"배아 등급: {self.embryo_grade}")
        if self.last_period_date:
            parts.append(f"직전 생리 시작일: {self.last_period_date.isoformat()}")
        if self.region:
            parts.append(f"지역: {self.region}")
        if self.amh is not None:
            parts.append(f"AMH: {self.amh} ng/mL")
        if self.diagnoses:
            parts.append(f"난임 진단: {', '.join(self.diagnoses)}")
        if self.infertility_duration:
            parts.append(f"난임 기간: {self.infertility_duration}")
        if self.marriage_status:
            label = "법적 혼인" if self.marriage_status == "legal" else "사실혼"
            parts.append(f"혼인 상태: {label}")
        if self.dual_income is not None:
            parts.append(f"맞벌이: {'예' if self.dual_income else '아니오'}")
        if self.partner_diagnosis:
            parts.append(f"남성 진단: {self.partner_diagnosis}")
        if self.frozen_embryo_count is not None:
            parts.append(f"동결배아: {self.frozen_embryo_count}개")
        if self.current_medications:
            parts.append(f"현재 약물: {', '.join(self.current_medications)}")
        if self.previous_treatments:
            prev_summary = [f"{t.get('type','?')} {t.get('cycle','')}회차({t.get('result','')})" for t in self.previous_treatments]
            parts.append(f"이전 시술: {', '.join(prev_summary)}")
        if self.notes:
            notes_summary = []
            for n in self.notes[-10:]:
                if isinstance(n, dict):
                    notes_summary.append(n.get("content", str(n)))
                else:
                    notes_summary.append(str(n))
            parts.append(f"채팅 기억: {' / '.join(notes_summary)}")

        return "\n".join(parts)


class ChatMessage(BaseModel):
    """단일 채팅 메시지"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    intent: Optional[str] = None          # 의도 분류 결과
    sources: Optional[list[str]] = None   # 참조 소스
    links: Optional[list[dict]] = None    # 유튜브/블로그 링크
    profile_updates: Optional[dict] = None  # 프로필 업데이트 (기록됨 카드)


class ChatSession(BaseModel):
    """채팅 세션"""
    session_id: str
    user_id: str
    messages: list[ChatMessage] = []
    proactive_delivered: list[str] = []
    created_at: datetime = Field(default_factory=datetime.now)

    def add_message(self, role: str, content: str, **kwargs):
        self.messages.append(ChatMessage(role=role, content=content, **kwargs))

    def get_recent_history(self, n: int = 20) -> list[dict]:
        """최근 N턴의 대화 히스토리를 LLM 형식으로 반환"""
        recent = self.messages[-n * 2:] if len(self.messages) > n * 2 else self.messages
        return [{"role": m.role, "content": m.content} for m in recent if m.role != "system"]


class RetrievedDocument(BaseModel):
    """벡터 검색 결과 단일 문서"""
    collection: str
    score: float
    content: str
    source: Optional[str] = None
    stage_ids: list[str] = []
    entity_ids: list[str] = []
    metadata: dict = {}


class PipelineResult(BaseModel):
    """파이프라인 전체 결과"""
    user_input: str
    preprocessed_input: str
    intent: str
    augmented_query: str
    retrieved_docs: list[RetrievedDocument] = []
    reranked_docs: list[RetrievedDocument] = []
    kg_context: str = ""
    response: str = ""
    sources_used: list[str] = []
    safety_flags: list[str] = []
    profile_updates: dict = {}
    info_gap_hint: Optional[str] = None
    links: list[dict] = []
    doctor_questions: list[str] = []
    suggested_replies: list[str] = []
