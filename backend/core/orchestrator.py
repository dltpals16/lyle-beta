"""
라일(Lyle) 챗봇 — 메인 오케스트레이터

Supervisor 기반 멀티에이전트 아키텍처:
- Supervisor: 의도 분류, 라우팅, 세션 관리
- CareAgent: medical + emotion (LangGraph 서브그래프)
- PolicyAgent: policy — 지원금/보험/비용 (LangGraph 서브그래프)
"""
from datetime import datetime
from typing import Optional
from models import UserProfile, ChatSession, PipelineResult
from firebase_config import add_doctor_questions, get_completed_not_followed_up, mark_followed_up, get_chat_messages

from core.llm_client import LLMClient
from core.term_preprocessor import TermPreprocessor
from core.intent_classifier import IntentClassifier
from core.query_augmenter import QueryAugmenter
from core.retriever import Retriever
from core.reranker import Reranker
from core.knowledge_enricher import KnowledgeEnricher
from core.response_generator import ResponseGenerator
from core.safety_filter import SafetyFilter
from core.info_gap_detector import InfoGapDetector
from core.care_agent import CareAgent
from core.policy_agent import PolicyAgent
from core.recommend_agent import RecommendAgent
from core.supervisor import Supervisor
from core.tools.tool_router import ToolRouter
from core.tools.drug_search import DrugSearchTool
from core.tools.hospital_search import HospitalSearchTool
from core.tools.shopping_search import ShoppingSearchTool


class LyleChatbot:
    """라일 챗봇 메인 오케스트레이터"""

    def __init__(self):
        print("=" * 50)
        print("라일(Lyle) 챗봇 초기화 중...")
        print("=" * 50)

        # LLM 클라이언트 (모든 모듈이 공유)
        llm = LLMClient()

        # 공유 모듈 초기화
        term_preprocessor = TermPreprocessor()
        intent_classifier = IntentClassifier(llm)
        query_augmenter = QueryAugmenter(llm)
        retriever = Retriever(llm)
        reranker = Reranker(llm)
        knowledge_enricher = KnowledgeEnricher()
        response_generator = ResponseGenerator(llm)
        safety_filter = SafetyFilter(llm)
        info_gap_detector = InfoGapDetector(knowledge_enricher)

        # Tool 초기화
        tool_router = ToolRouter(llm)
        drug_search = DrugSearchTool()
        hospital_search = HospitalSearchTool()
        shopping_search = ShoppingSearchTool()

        # 에이전트 초기화
        care_agent = CareAgent(
            query_augmenter=query_augmenter,
            retriever=retriever,
            reranker=reranker,
            knowledge_enricher=knowledge_enricher,
            response_generator=response_generator,
            safety_filter=safety_filter,
            info_gap_detector=info_gap_detector,
            tool_router=tool_router,
            drug_search=drug_search,
            hospital_search=hospital_search,
        )
        policy_agent = PolicyAgent(
            query_augmenter=query_augmenter,
            retriever=retriever,
            reranker=reranker,
            knowledge_enricher=knowledge_enricher,
            response_generator=response_generator,
            safety_filter=safety_filter,
            info_gap_detector=info_gap_detector,
            llm_client=llm,
        )
        recommend_agent = RecommendAgent(
            shopping_search=shopping_search,
            drug_search=drug_search,
        )

        # Supervisor 초기화
        self.supervisor = Supervisor(
            llm=llm,
            term_preprocessor=term_preprocessor,
            intent_classifier=intent_classifier,
            safety_filter=safety_filter,
            care_agent=care_agent,
            policy_agent=policy_agent,
            recommend_agent=recommend_agent,
        )

        # 세션/프로필 저장소 (메모리, 실제 운영 시 DB로 교체)
        self.sessions: dict[str, ChatSession] = {}
        self.profiles: dict[str, UserProfile] = {}

        print("라일 챗봇 초기화 완료\n")

    # ═══════════════════════════════════════
    # 메인 대화 처리
    # ═══════════════════════════════════════

    def chat(self, user_id: str, message: str, status_callback=None, conversation_id: str = None) -> PipelineResult:
        """메인 대화 처리 — Supervisor에게 위임"""
        profile = self.profiles.get(user_id)
        if not profile:
            return PipelineResult(
                user_input=message,
                preprocessed_input=message,
                intent="error",
                augmented_query="",
                response="먼저 프로필을 등록해주세요. register_user()를 호출해주세요.",
            )

        session = self._get_or_create_session(user_id, conversation_id)

        # ── 완료된 진료 질문 후속 처리 (대화 시작 시 주입) ──
        followup_questions = get_completed_not_followed_up(user_id)
        if followup_questions:
            followup_hint = self._build_followup_hint(followup_questions)
            # 원래 메시지 앞에 후속 컨텍스트 주입
            message_with_context = f"[시스템 컨텍스트] {followup_hint}\n\n사용자 메시지: {message}"
        else:
            message_with_context = message

        # Supervisor에게 위임
        result = self.supervisor.chat(
            user_id=user_id,
            message=message_with_context,
            profile=profile,
            session=session,
            status_callback=status_callback,
        )

        # 프로필 업데이트 적용 (Supervisor가 메모리 내 프로필은 이미 업데이트함)
        # Firestore 저장은 server.py에서 처리

        # ── 진료 질문 Firestore 저장 ──
        if result.doctor_questions:
            add_doctor_questions(user_id, result.doctor_questions)

        # ── 후속 질문 완료 마킹 ──
        for fq in followup_questions:
            mark_followed_up(user_id, fq["id"])

        print(f"\n{'='*50}")
        return result

    def _build_followup_hint(self, questions: list) -> str:
        """완료된 진료 질문에 대해 후속 질문 컨텍스트 생성"""
        items = [q["content"] for q in questions]
        hint = (
            "사용자가 최근 진료에서 다음 항목을 확인했습니다. "
            "자연스럽게 '선생님께서 뭐라고 하셨어요?' 식으로 후속 질문을 해주세요:\n"
        )
        for i, item in enumerate(items, 1):
            hint += f"  {i}. {item}\n"
        return hint

    # ═══════════════════════════════════════
    # 유저 관리
    # ═══════════════════════════════════════

    def register_user(self, profile: UserProfile) -> str:
        """유저 프로필 등록"""
        self.profiles[profile.user_id] = profile
        return f"{profile.name}님 프로필 등록 완료 (stage: {profile.treatment_stage})"

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        return self.profiles.get(user_id)

    def update_profile(self, user_id: str, **kwargs) -> Optional[UserProfile]:
        profile = self.profiles.get(user_id)
        if not profile:
            return None
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.updated_at = datetime.now()
        return profile

    # ═══════════════════════════════════════
    # 세션 관리
    # ═══════════════════════════════════════

    def _get_or_create_session(self, user_id: str, conversation_id: str = None) -> ChatSession:
        session_key = f"{user_id}_{conversation_id}" if conversation_id else user_id
        if session_key not in self.sessions:
            session = ChatSession(
                session_id=f"session_{session_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id=user_id,
            )
            # Firebase에서 기존 대화 히스토리 복원 (서버 재시작 대응)
            if conversation_id:
                try:
                    saved_msgs = get_chat_messages(user_id, conversation_id)
                    if saved_msgs:
                        for m in saved_msgs:
                            session.add_message(
                                role=m.get("role", "user"),
                                content=m.get("content", ""),
                                links=m.get("links", []),
                            )
                        print(f"[Session] Firebase에서 히스토리 복원: {user_id}/{conversation_id} ({len(saved_msgs)}건)")
                except Exception as e:
                    print(f"[Session] 히스토리 복원 실패: {e}")
            self.sessions[session_key] = session
        return self.sessions[session_key]

    def reset_session(self, user_id: str):
        """세션 + 대화 상태 초기화"""
        if user_id in self.sessions:
            del self.sessions[user_id]
        self.supervisor.reset_state(user_id)
