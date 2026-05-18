"""
라일(Lyle) 챗봇 — 전역 설정 v2

변경 사항:
- Intent: 6개 → 4개 (medical, emotion, policy, out_of_scope)
- Weight: light/heavy 추가
- INTENT_COLLECTION_WEIGHTS: 새 intent 체계에 맞춰 업데이트
- MEDICAL_BOUNDARY_KEYWORDS: out_of_scope가 아닌 hard boundary로 이동 (프롬프트에서 처리)
"""
import os
from enum import Enum

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────────────────────
# Firebase 설정
# ──────────────────────────────────────────
FIREBASE_CREDENTIAL_PATH = "/mnt/aix22401/라일/lyle-beta/lyle-beta-firebase-adminsdk-fbsvc-d5cb1d3424.json"

# ──────────────────────────────────────────
# LLM 설정
# ──────────────────────────────────────────
LLM_PROVIDER = "openai"

# OpenAI
OPENAI_MODEL_MAIN = "gpt-4o"            # 답변 생성용
OPENAI_MODEL_LIGHT = "gpt-4o-mini"      # 의도 분류, 리랭킹 등 경량 작업용
OPENAI_MAX_TOKENS = 1500

# OpenAI (임베딩용)
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_EMBEDDING_DIM = 3072

# ──────────────────────────────────────────
# Qdrant 설정
# ──────────────────────────────────────────
QDRANT_PATH = os.path.join(BASE_DIR, "data", "vectorstore")  # 로컬 모드
QDRANT_COLLECTIONS = {
    "pdf_qna": {"priority": 1, "description": "병원 가이드북 Q&A"},
    "pdf_chunk": {"priority": 1, "description": "병원 가이드북 청크"},
    "youtube_qna": {"priority": 2, "description": "유튜브 전문가 Q&A"},
    "blog": {"priority": 3, "description": "블로그 경험담"},
    "web_reference": {"priority": 1, "description": "웹 레퍼런스 (의학 참고자료)"},
    "policy_chunk": {"priority": 1, "description": "정책/지원사업 안내"},
}

# ──────────────────────────────────────────
# Knowledge Graph 파일 경로
# ──────────────────────────────────────────
KG_PATH = os.path.join(BASE_DIR, "data", "knowledge_graph.json")
TRIPLES_PATH = os.path.join(BASE_DIR, "data", "triples.json")
TIMELINE_PATH = os.path.join(BASE_DIR, "data", "timeline_extension.json")
TERM_DICT_PATH = os.path.join(BASE_DIR, "data", "term_dictionary.json")

# ──────────────────────────────────────────
# 정책 데이터 경로 (InfoAgent PolicyEngine용)
# ──────────────────────────────────────────
POLICY_DATA_DIR = os.path.join(BASE_DIR, "data", "지원사업")
POLICY_DATA_FILES = {
    "tables": "chunks/policy_tables.json",
    "application_flow": "infertility_support_application_flow.json",
    "tax_deduction": "tax_deduction_infertility_v2.json",
    "nhi_coverage": "nhi_infertility_coverage_v2.json",
    "services": "infertility_services_dataset.json",
    "hospitals": "infertility_hospitals_hira.json",
    "bokjiro": "bokjiro_infertility.json",
}

# ──────────────────────────────────────────
# 검색 설정
# ──────────────────────────────────────────
RETRIEVAL_TOP_K = 10          # 컬렉션당 초기 검색 수
RERANK_TOP_N = 8              # 리랭킹 후 최종 수 (다양한 문서 활용)
SIMILARITY_THRESHOLD = 0.35   # 이 이하면 "답변 불가" 처리

# 의도별 컬렉션 가중치 (검색 결과 수 배분)
# ※ heavy path에서만 사용됨 (light는 검색 스킵)
INTENT_COLLECTION_WEIGHTS = {
    "medical":  {"pdf_qna": 2, "pdf_chunk": 2, "youtube_qna": 2, "blog": 2, "web_reference": 2},
    "emotion":  {"pdf_qna": 1, "pdf_chunk": 1, "youtube_qna": 2, "blog": 5, "web_reference": 1},
    "policy":   {"pdf_qna": 0, "pdf_chunk": 0, "youtube_qna": 0, "blog": 0, "web_reference": 0, "policy_chunk": 8},
    "out_of_scope": {},  # 검색 안 함
}

# ──────────────────────────────────────────
# 대화 히스토리 설정
# ──────────────────────────────────────────
MAX_HISTORY_TURNS = 20  # 최근 N턴 유지
MAX_CONTEXT_TOKENS = 6000  # LLM에 전달할 최대 컨텍스트

# ──────────────────────────────────────────
# 안전 필터
# ──────────────────────────────────────────
CRISIS_KEYWORDS = [
    "죽고 싶", "자살", "자해", "끝내고 싶", "살기 싫",
    "더 이상 못", "포기하고 싶", "의미가 없",
]

# ※ v1의 MEDICAL_BOUNDARY_KEYWORDS는 삭제
# → 약 용량 변경, 병원 추천 등은 intent classifier가 아닌
#   SYSTEM_BASE의 hard boundary + safety_filter에서 처리

# ──────────────────────────────────────────
# 의도 & 경중 Enum
# ──────────────────────────────────────────
class Intent(str, Enum):
    MEDICAL = "medical"               # 증상, 시술 과정, 일정, 약물, 수치, 부작용
    EMOTION = "emotion"               # 감정 지지, 관계 고민, 스트레스
    POLICY = "policy"                 # 지원금, 보험, 비용, 혜택
    RECOMMENDATION = "recommendation" # 영양제/진단기기/운동도구/이완용품 등 헬스케어 제품 추천
    OUT_OF_SCOPE = "out_of_scope"     # 난임과 무관한 질문


class Weight(str, Enum):
    LIGHT = "light"   # LLM 자체 지식으로 충분 → 검색 스킵
    HEAVY = "heavy"   # RAG 파이프라인 필요 → 풀 검색


# ──────────────────────────────────────────
# 시술 단계 매핑
# ──────────────────────────────────────────
STAGE_MAPPING = {
    "임신 준비": "S01",
    "난임 의심": "S02",
    "난임 검사": "S03",
    "배란기 성관계/약물 치료": "S04",
    "수술적 치료": "S05",
    "인공수정": "S06_IUI",
    "체외수정": "S06_IVF",
    "동결배아 이식": "S06_FET",
    "착상전 유전자검사": "S06_PGT",
    "임신 확인": "S07",
    "재시도": "S08",
    "종료": "S09",
    # 유저 친화적 별칭
    "시험관": "S06_IVF",
    "IVF": "S06_IVF",
    "ivf": "S06_IVF",
    "인공수정(IUI)": "S06_IUI",
    "iui": "S06_IUI",
    "FET": "S06_FET",
    "fet": "S06_FET",
    "prep": "S01",
    "timing": "S04",
    "retry": "S08",
    "준비 중": "S01",
}
