# Lyle (라일) — 난임 치료 AI 케어 컴패니언

난임 시술/임신 준비 여정을 함께하는 AI 에이전트 서비스입니다.

## 서비스 URL
- **Production**: https://lyle-mvp.onrender.com

## 구조

```
lyle-beta/
├── frontend/          # React + Vite 프론트엔드
│   ├── src/
│   │   ├── screens/
│   │   │   ├── MedicalScreens.jsx    # 난임 시술 모드
│   │   │   ├── NaturalScreens.jsx    # 자연임신 모드
│   │   │   └── OnboardingScreen.jsx  # 온보딩
│   │   ├── App.jsx
│   │   ├── styles/theme.js
│   │   └── data/timeline.js
│   ├── package.json
│   └── vite.config.js
│
├── backend/           # FastAPI + LangGraph 백엔드
│   ├── api/server.py              # FastAPI 서버 + SSE 스트리밍
│   ├── core/
│   │   ├── orchestrator.py        # 메인 오케스트레이터
│   │   ├── supervisor.py          # 의도 분류 + 에이전트 라우팅
│   │   ├── care_agent.py          # LangGraph 기반 의료 에이전트
│   │   ├── response_generator.py  # LLM 응답 생성
│   │   ├── intent_classifier.py   # 의도/경중 분류
│   │   ├── retriever.py           # Qdrant 벡터 검색
│   │   ├── reranker.py            # LLM 기반 재순위
│   │   ├── knowledge_enricher.py  # KG 보강
│   │   └── profile_updater.py     # 프로필 자동 업데이트
│   ├── prompts/
│   │   ├── templates.py           # 난임 모드 프롬프트
│   │   └── templates_natural.py   # 자연임신 모드 프롬프트
│   ├── services/
│   │   ├── alimtalk.py            # 카카오 알림톡 발송
│   │   └── notification_scheduler.py  # 알림 스케줄러
│   ├── data/                      # KG, 타임라인, 지원사업 데이터
│   ├── config.py
│   ├── models.py
│   ├── firebase_config.py
│   └── requirements.txt
│
└── README.md
```

## 기술 스택

### Frontend
- React 18 + Vite
- Firebase Auth (닉네임 기반)
- SSE (Server-Sent Events) 스트리밍

### Backend
- FastAPI + Uvicorn
- LangGraph (에이전트 워크플로우)
- OpenAI GPT-4o / GPT-4o-mini
- Qdrant Cloud (벡터 DB, 4,051건)
- Firebase Firestore (유저/대화/세션)
- APScheduler (알림톡 스케줄러)

### Data
- Knowledge Graph: 144개 엔티티 + 255개 관계
- 타임라인: IVF/IUI/타이밍법/FET 단계별 진행
- 지원사업: 165건 (전국 지자체)
- 난임 지정 병원: 258개

## 에이전트 아키텍처

```
사용자 메시지
    │
    ▼
[Supervisor] → 의도 분류 (medical/emotion/policy/out_of_scope)
    │
    ├── medical/emotion → [CareAgent]
    │   ├── classify_weight (light/heavy)
    │   ├── light → inmemory_lookup (KG + Timeline)
    │   ├── heavy → retrieve (Qdrant) → rerank → generate_response
    │   └── 병렬: safety_check + extract_doctor_questions + generate_suggestions
    │
    └── policy → [PolicyAgent]
        └── policy_search → generate_response
```

## 주요 기능

- **멀티모달 RAG**: 6개 Qdrant 컬렉션 (의학 Q&A, 블로그, 정책 등)
- **Knowledge Graph 보강**: 엔티티/트리플/타임라인 기반 맥락 주입
- **프로필 자동 업데이트**: 대화에서 시술 단계, 약물, 수치 자동 추출
- **카카오 알림톡**: 복약 리마인더, 메디컬 체크, 가임기 알림
- **자연임신/난임 모드 분리**: 프론트+프롬프트+지원금 각각 독립

## Setup

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
# .env 파일에 OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY 등 설정
uvicorn api.server:app --host 0.0.0.0 --port 8000
```
