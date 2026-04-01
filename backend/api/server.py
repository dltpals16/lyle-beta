"""
라일(Lyle) 챗봇 - FastAPI 서버
Firebase Firestore 연동, 프론트엔드 프로필과 동기화
"""
import pathlib
from dotenv import load_dotenv
_env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)  # 프로젝트 루트 .env 로드

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import Optional
import json
import os
import asyncio
import threading

from models import UserProfile, Gender
from core.orchestrator import LyleChatbot
from firebase_config import (
    get_user_profile as fb_get_profile,
    save_user_profile as fb_save_profile,
    update_user_profile as fb_update_profile,
    save_chat_messages as fb_save_chat,
    get_chat_messages as fb_get_chat,
    update_conversation_title as fb_update_title,
    list_conversations as fb_list_conversations,
    delete_conversation as fb_delete_conversation,
    star_conversation as fb_star_conversation,
    rename_conversation as fb_rename_conversation,
    get_doctor_questions as fb_get_dq,
    check_doctor_question as fb_check_dq,
    uncheck_doctor_question as fb_uncheck_dq,
    delete_doctor_question as fb_delete_dq,
    add_doctor_questions as fb_add_dq,
    save_notes as fb_save_notes,
    get_notes as fb_get_notes,
    delete_note as fb_delete_note,
    save_feedback as fb_save_feedback,
    save_analytics_events as fb_save_analytics,
    db,
)

app = FastAPI(
    title="라일(Lyle) AI 챗봇",
    description="난임 시술 동반자 AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

chatbot: LyleChatbot = None


@app.on_event("startup")
async def startup():
    global chatbot
    chatbot = LyleChatbot()

    # 알림톡 스케줄러 시작
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from services.notification_scheduler import check_and_send_notifications
        scheduler = BackgroundScheduler(timezone="Asia/Seoul")
        scheduler.add_job(check_and_send_notifications, "cron", minute="0,30")  # 30분 단위 실행
        scheduler.start()
        print("[스케줄러] 알림톡 스케줄러 시작 완료")
    except Exception as e:
        print(f"[스케줄러] 시작 실패: {e}")


# ── Request/Response 모델 ──

class ChatRequest(BaseModel):
    uid: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: str
    sources: list[str]
    safety_flags: list[str]
    profile_updates: dict
    links: list[dict] = []
    conversation_id: str
    suggested_replies: list[str] = []


# ── 헬퍼: Firestore 프로필 → UserProfile 변환 ──

def _firestore_to_profile(uid: str, data: dict) -> UserProfile:
    """프론트엔드 Firestore 필드명 → 백엔드 UserProfile 매핑"""
    # birthYear → birth_date 변환
    birth_year = data.get("birthYear", 2000)
    try:
        birth_date = date(int(birth_year), 1, 1)
    except (ValueError, TypeError):
        birth_date = date(2000, 1, 1)

    # periodDate → last_period_date
    period_str = data.get("periodDate", "")
    last_period = None
    if period_str:
        try:
            parts = period_str.split("-")
            last_period = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            pass

    # stage ID → 한글 시술 단계
    from config import STAGE_MAPPING
    stage_id = data.get("stage", "prep")
    reverse_stage = {v: k for k, v in STAGE_MAPPING.items()}
    # 프론트 stage id → 매핑
    FRONT_STAGE_MAP = {
        "prep": "임신 준비",
        "testing": "난임 검사",
        "iui": "인공수정",
        "ivf": "체외수정",
        "fet": "동결배아 이식",
        "retry": "재시도",
    }
    treatment_stage = FRONT_STAGE_MAP.get(stage_id, stage_id)

    # region: region1 (시/도) + region2 (구/군)
    region1 = data.get("region1", "")
    region2 = data.get("region2", "")
    region = f"{region1} {region2}".strip() if region2 else region1

    # amh: 문자열 → float
    amh_val = data.get("amh", "")
    amh = None
    if amh_val:
        try:
            amh = float(amh_val)
        except (ValueError, TypeError):
            pass

    return UserProfile(
        user_id=uid,
        name=data.get("displayName", ""),
        mode=data.get("mode", "medical"),
        birth_date=birth_date,
        gender=Gender(data.get("gender", "female")),
        last_period_date=last_period,
        treatment_stage=treatment_stage,
        treatment_cycle=int(data.get("cycle")) if str(data.get("cycle", "")).isdigit() else 0,
        protocol=data.get("protocol") or None,
        region=region,
        amh=amh,
        diagnoses=data.get("diagnoses", []),
        infertility_duration=data.get("infertilityDuration") or None,
        marriage_status=data.get("marriageStatus") or None,
        dual_income=data.get("dual_income"),
        partner_diagnosis=data.get("partner_diagnosis") or None,
        frozen_embryo_count=data.get("frozen_embryo_count"),
        current_medications=data.get("current_medications", []),
        previous_treatments=data.get("previous_treatments", []),
        notes=data.get("chatMemory", []),
    )


# ── 백엔드 필드명 → Firestore 필드명 변환 ──

# 백엔드 treatment_stage 한글 → 프론트 stage ID (키워드 기반 매칭)
_STAGE_KEYWORDS = [
    (["시험관", "체외수정", "ivf", "IVF"], "ivf"),
    (["인공수정", "iui", "IUI"], "iui"),
    (["동결배아", "동결이식", "fet", "FET"], "fet"),
    (["재시도", "다시"], "retry"),
    (["난임 검사", "검사"], "testing"),
    (["임신 준비", "준비"], "prep"),
]

# 백엔드 필드명 → Firestore 필드명
_FIELD_TO_FIRESTORE = {
    "treatment_stage": "stage",
    "treatment_cycle": "cycle",
    "current_phase": "current_phase",
    "protocol": "protocol",
    "amh": "amh",
    "diagnoses": "diagnoses",
    "infertility_duration": "infertilityDuration",
    "marriage_status": "marriageStatus",
    "dual_income": "dual_income",
    "partner_diagnosis": "partner_diagnosis",
    "frozen_embryo_count": "frozen_embryo_count",
    "current_medications": "current_medications",
}


def _convert_profile_updates(updates: dict) -> dict:
    """PipelineResult.profile_updates → Firestore 업데이트 dict 변환"""
    fields = updates.get("fields", {})
    if not fields:
        return {}

    firestore_data = {}
    for backend_key, value in fields.items():
        fs_key = _FIELD_TO_FIRESTORE.get(backend_key)
        if not fs_key:
            continue

        # treatment_stage: 한글 → 프론트 stage ID로 변환 (키워드 매칭)
        if backend_key == "treatment_stage":
            matched = None
            for keywords, stage_id in _STAGE_KEYWORDS:
                if any(kw in value for kw in keywords):
                    matched = stage_id
                    break
            if matched:
                value = matched
            else:
                continue  # 매핑 안 되면 저장하지 않음

        firestore_data[fs_key] = value

    # current_phase 변경 시 phase_changed_at 자동 추가
    if "current_phase" in firestore_data:
        from datetime import datetime
        firestore_data["phase_changed_at"] = datetime.now().strftime("%Y-%m-%d")

    return firestore_data


# ── 엔드포인트 ──

@app.post("/chat", response_model=ChatResponse, summary="채팅 메시지 전송")
async def chat(req: ChatRequest):
    import uuid

    # Firestore에서 프로필 로드 (게스트는 프로필 없이 진행)
    is_guest = req.uid.startswith("guest_")
    fb_data = fb_get_profile(req.uid) if not is_guest else None
    if not is_guest and (not fb_data or not fb_data.get("onboardingComplete")):
        raise HTTPException(status_code=404, detail="온보딩을 먼저 완료해주세요.")

    # Firestore → UserProfile 변환 (게스트는 빈 프로필)
    profile = _firestore_to_profile(req.uid, fb_data or {})

    # 메모리에 프로필 등록 (없으면)
    if not chatbot.get_profile(req.uid):
        chatbot.register_user(profile)
    else:
        chatbot.profiles[req.uid] = profile

    # 대화 ID: 프론트에서 보내거나 새로 생성
    conv_id = req.conversation_id or str(uuid.uuid4())[:8]

    # 파이프라인 실행
    result = chatbot.chat(req.uid, req.message, conversation_id=conv_id)

    # 프로필 자동 업데이트가 감지되었으면 Firestore에도 저장
    if result.profile_updates:
        firestore_updates = _convert_profile_updates(result.profile_updates)
        if firestore_updates:
            fb_update_profile(req.uid, firestore_updates)

    # notes(채팅 기억)를 Firestore에도 저장
    notes_list = result.profile_updates.get("notes", [])
    if notes_list:
        profile = chatbot.profiles.get(req.uid)
        if profile:
            fb_save_notes(req.uid, profile.notes)

    # 채팅 히스토리 Firestore에 저장
    session_key = f"{req.uid}_{conv_id}"
    session = chatbot.sessions.get(session_key)
    if session:
        messages = [
            {"role": m.role, "content": m.content}
            for m in session.messages[-40:]
        ]
        fb_save_chat(req.uid, messages, conv_id)

        # 첫 번째 메시지일 때 대화 제목 자동 생성
        user_msgs = [m for m in messages if m["role"] == "user"]
        if len(user_msgs) == 1:
            title = _generate_chat_title(user_msgs[0]["content"])
            fb_update_title(req.uid, conv_id, title)

    return ChatResponse(
        response=result.response,
        intent=result.intent,
        sources=result.sources_used,
        safety_flags=result.safety_flags,
        profile_updates=result.profile_updates,
        links=result.links,
        conversation_id=conv_id,
        suggested_replies=result.suggested_replies,
    )


@app.post("/chat/stream", summary="채팅 메시지 전송 (SSE 스트리밍)")
async def chat_stream(req: ChatRequest):
    import uuid

    is_guest = req.uid.startswith("guest_")
    fb_data = fb_get_profile(req.uid) if not is_guest else None
    if not is_guest and (not fb_data or not fb_data.get("onboardingComplete")):
        raise HTTPException(status_code=404, detail="온보딩을 먼저 완료해주세요.")

    profile = _firestore_to_profile(req.uid, fb_data or {})
    if not chatbot.get_profile(req.uid):
        chatbot.register_user(profile)
    else:
        chatbot.profiles[req.uid] = profile

    conv_id = req.conversation_id or str(uuid.uuid4())[:8]

    # 비동기 큐: SSE 이벤트 전달용
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def status_callback(message: str):
        """LangGraph 노드에서 호출 — 스레드 safe하게 큐에 넣음"""
        loop.call_soon_threadsafe(queue.put_nowait, {"type": "status", "message": message})

    def run_chat():
        """별도 스레드에서 chatbot 실행 + Firebase 저장 (SSE 연결과 무관하게 항상 실행)"""
        try:
            # 유저 메시지 선행 저장 — 응답 실패해도 "뭘 물어봤는지"는 남음
            try:
                session_key = f"{req.uid}_{conv_id}"
                session = chatbot.sessions.get(session_key)
                if session:
                    user_msgs = [{"role": m.role, "content": m.content, "links": getattr(m, 'links', None) or []} for m in session.messages[-40:]]
                    fb_save_chat(req.uid, user_msgs, conv_id)
            except Exception:
                pass

            result = chatbot.chat(req.uid, req.message, status_callback=status_callback, conversation_id=conv_id)

            # Firebase 저장 — SSE 전송 전에 항상 실행
            try:
                if result.profile_updates:
                    firestore_updates = _convert_profile_updates(result.profile_updates)
                    if firestore_updates:
                        fb_update_profile(req.uid, firestore_updates)
                    notes_list = result.profile_updates.get("notes", [])
                    if notes_list:
                        prof = chatbot.profiles.get(req.uid)
                        if prof:
                            fb_save_notes(req.uid, prof.notes)
                session_key = f"{req.uid}_{conv_id}"
                session = chatbot.sessions.get(session_key)
                if session:
                    messages = [{"role": m.role, "content": m.content, "links": getattr(m, 'links', None) or [], "sources": getattr(m, 'sources', None) or [], "profile_updates": getattr(m, 'profile_updates', None) or {}} for m in session.messages[-40:]]
                    # 마지막 assistant 메시지에 suggested_replies 추가
                    if messages and messages[-1]["role"] == "assistant" and result.suggested_replies:
                        messages[-1]["suggested_replies"] = result.suggested_replies
                    fb_save_chat(req.uid, messages, conv_id)
                    user_msgs = [m for m in messages if m["role"] == "user"]
                    if len(user_msgs) == 1:
                        title = _generate_chat_title(user_msgs[0]["content"])
                        fb_update_title(req.uid, conv_id, title)
            except Exception as save_err:
                print(f"[Firebase 저장 오류] {save_err}")

            loop.call_soon_threadsafe(queue.put_nowait, {"type": "response", "data": result})
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "message": str(e)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)  # 종료 신호

    async def event_generator():
        # chatbot을 스레드에서 실행
        thread = threading.Thread(target=run_chat, daemon=True)
        thread.start()

        while True:
            item = await queue.get()
            if item is None:
                break
            if item["type"] == "status":
                yield f"data: {json.dumps({'type': 'status', 'message': item['message']}, ensure_ascii=False)}\n\n"
            elif item["type"] == "response":
                result = item["data"]
                # Firebase 저장은 run_chat() 스레드에서 이미 완료됨
                payload = {
                    "type": "response",
                    "response": result.response,
                    "intent": result.intent,
                    "sources": result.sources_used,
                    "safety_flags": result.safety_flags,
                    "profile_updates": result.profile_updates,
                    "links": result.links,
                    "conversation_id": conv_id,
                    "suggested_replies": result.suggested_replies,
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            elif item["type"] == "error":
                yield f"data: {json.dumps({'type': 'error', 'message': item['message']}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _generate_chat_title(first_message: str) -> str:
    """첫 사용자 메시지에서 대화 제목 생성 (간단 요약)"""
    msg = first_message.strip()
    if len(msg) <= 20:
        return msg
    # 물음표가 있으면 첫 질문까지
    if "?" in msg:
        return msg[:msg.index("?") + 1][:25]
    if "?" in msg:
        return msg[:msg.index("?") + 1][:25]
    return msg[:20] + "…"


@app.get("/profile/{uid}", summary="유저 프로필 조회")
async def get_profile(uid: str):
    fb_data = fb_get_profile(uid)
    if not fb_data:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다")
    return fb_data


@app.post("/reset/{uid}", summary="세션 초기화")
async def reset_session(uid: str):
    chatbot.reset_session(uid)
    return {"status": "ok", "message": "세션이 초기화되었습니다"}


@app.get("/subsidy/{uid}", summary="맞춤 지원금 정보 조회")
async def get_subsidy(uid: str):
    fb_data = fb_get_profile(uid)
    if not fb_data:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다")

    stage_id = fb_data.get("stage", "prep")
    cycle = int(fb_data.get("cycle")) if str(fb_data.get("cycle", "")).isdigit() else 0
    region1 = fb_data.get("region1", "")
    region2 = fb_data.get("region2", "")
    marriage = fb_data.get("marriageStatus")

    # 정책 테이블 로드
    from config import POLICY_DATA_DIR, POLICY_DATA_FILES
    tables_path = os.path.join(POLICY_DATA_DIR, POLICY_DATA_FILES["tables"])
    try:
        with open(tables_path, "r", encoding="utf-8") as f:
            tables = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        tables = {}

    amount_data = tables.get("support_amount_2026", {}).get("data", {})
    count_data = tables.get("treatment_count_2026", {}).get("data", {})
    copay_data = tables.get("insurance_copay_2026", {}).get("data", {})

    # 혼인 여부 → 자격 판단
    eligible = marriage in ("legal", "defacto")

    # 시술 단계 → 지원금 매핑
    STAGE_LABEL = {
        "prep": "임신 준비", "testing": "난임 검사", "iui": "인공수정 (IUI)",
        "ivf": "체외수정 (IVF)", "fet": "동결배아 이식 (FET)", "retry": "재시도",
    }
    stage_label = STAGE_LABEL.get(stage_id, stage_id)

    # 시술별 금액·횟수 계산
    if stage_id == "iui":
        per_session = amount_data.get("인공수정", {}).get("최대금액", 300000)
        max_sessions = count_data.get("인공수정", {}).get("총_횟수", 5)
        treatment_name = "인공수정"
    elif stage_id == "fet":
        per_session = amount_data.get("체외수정_동결배아", {}).get("최대금액", 500000)
        max_sessions = count_data.get("체외수정", {}).get("총_횟수", 20)
        treatment_name = "동결배아 이식"
    elif stage_id == "ivf":
        per_session = amount_data.get("체외수정_신선배아", {}).get("최대금액", 1100000)
        max_sessions = count_data.get("체외수정", {}).get("총_횟수", 20)
        treatment_name = "체외수정 (신선배아)"
    else:
        # prep, testing, retry → 체외수정 기준으로 일반 안내
        per_session = amount_data.get("체외수정_신선배아", {}).get("최대금액", 1100000)
        max_sessions = count_data.get("체외수정", {}).get("총_횟수", 20)
        treatment_name = "체외수정 (신선배아)"

    remaining = max(0, max_sessions - cycle)
    per_session_display = f"최대 {per_session // 10000}만원"
    copay_rate = copay_data.get("본인부담률", "30%")

    # 총 예상 지원금 (이번 회차 기준)
    total_estimate = per_session
    total_display = f"최대 {total_estimate // 10000}만원"

    # 카드 데이터
    cards = [
        {
            "label": "건강보험 적용",
            "value": f"본인부담 {copay_rate}",
            "sub": "연령 무관 일괄 적용 (2024.11~)",
        },
        {
            "label": "정부 난임시술 지원금",
            "value": f"회당 {per_session_display}",
            "sub": f"{treatment_name} 기준 · 통지서 발급 필수",
            "link": "https://www.gov.kr/search/apply?query=%EB%82%9C%EC%9E%84",
        },
        {
            "label": "지원 횟수",
            "value": f"최대 {max_sessions}회",
            "sub": f"출산당 기준 ({treatment_name})",
        },
        {
            "label": "난임치료 휴가",
            "value": "연 6일",
            "sub": "최초 2일 유급 (근로기준법)",
        },
    ]

    return {
        "eligible": eligible,
        "marriageStatus": marriage,
        "stage": stage_label,
        "region": f"{region1} {region2}".strip(),
        "totalEstimate": total_display,
        "perSession": per_session_display,
        "cards": cards,
        "notice": "시술 시작 전에 보건소 지원결정통지서를 반드시 발급받으세요. 소급 지원이 불가합니다.",
        "source": "2026년 모자보건사업 안내",
    }


@app.get("/chat/history/{uid}", summary="대화 목록 조회")
async def get_chat_history(uid: str):
    """사용자의 모든 대화 목록을 반환합니다."""
    conversations = fb_list_conversations(uid)
    return {"conversations": conversations}


@app.get("/chat/history/{uid}/{conversation_id}", summary="특정 대화 내역 조회")
async def get_conversation(uid: str, conversation_id: str):
    """특정 대화의 메시지를 반환합니다."""
    messages = fb_get_chat(uid, conversation_id)
    return {"messages": messages}


@app.delete("/chat/history/{uid}/{conversation_id}", summary="대화 삭제")
async def delete_conversation(uid: str, conversation_id: str):
    """특정 대화를 삭제합니다."""
    fb_delete_conversation(uid, conversation_id)
    return {"status": "ok"}


@app.post("/chat/history/{uid}/{conversation_id}/star", summary="대화 즐겨찾기 토글")
async def star_conversation(uid: str, conversation_id: str, starred: bool = True):
    fb_star_conversation(uid, conversation_id, starred)
    return {"status": "ok", "starred": starred}


@app.post("/chat/history/{uid}/{conversation_id}/rename", summary="대화 이름 변경")
async def rename_conversation(uid: str, conversation_id: str, title: str = ""):
    fb_rename_conversation(uid, conversation_id, title)
    return {"status": "ok", "title": title}


# ── 진료 질문 체크리스트 ──

@app.get("/doctor-questions/{uid}", summary="진료 질문 체크리스트 조회")
async def get_doctor_questions(uid: str, only_pending: bool = False):
    """홈 화면 체크리스트용 진료 질문 목록"""
    questions = fb_get_dq(uid, only_pending=only_pending)
    return {"questions": questions}


@app.post("/doctor-questions/{uid}/{question_id}/check", summary="진료 질문 체크 (완료)")
async def check_question(uid: str, question_id: str):
    """사용자가 진료 후 체크 → completed 상태로 전환"""
    result = fb_check_dq(uid, question_id)
    if not result:
        raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
    return result


@app.post("/doctor-questions/{uid}/{question_id}/uncheck", summary="진료 질문 체크 해제")
async def uncheck_question(uid: str, question_id: str):
    result = fb_uncheck_dq(uid, question_id)
    if not result:
        raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
    return result


@app.delete("/doctor-questions/{uid}/{question_id}", summary="진료 질문 삭제")
async def delete_question(uid: str, question_id: str):
    fb_delete_dq(uid, question_id)
    return {"status": "ok"}


class AddQuestionRequest(BaseModel):
    content: str


@app.post("/doctor-questions/{uid}", summary="진료 질문 직접 추가")
async def add_question(uid: str, req: AddQuestionRequest):
    added = fb_add_dq(uid, [req.content])
    if not added:
        return {"status": "duplicate", "question": None}
    return {"status": "ok", "question": added[0]}


# ── 채팅 기억 (Notes) ──

@app.get("/notes/{uid}", summary="채팅 기억 조회")
async def get_notes_endpoint(uid: str):
    notes = fb_get_notes(uid)
    return {"notes": notes}


@app.delete("/notes/{uid}/{note_id}", summary="채팅 기억 삭제")
async def delete_note_endpoint(uid: str, note_id: str):
    deleted = fb_delete_note(uid, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="해당 기억을 찾을 수 없습니다.")
    return {"ok": True}


# ── 기록 (Records) ──

@app.get("/records/{uid}", summary="기록 조회")
async def get_records(uid: str):
    try:
        doc = db.collection("users").document(uid).collection("records").document("all").get()
        if doc.exists:
            return {"records": doc.to_dict().get("items", [])}
        return {"records": []}
    except:
        return {"records": []}

@app.post("/records/{uid}", summary="기록 추가")
async def add_record(uid: str, request: Request):
    record = await request.json()
    doc_ref = db.collection("users").document(uid).collection("records").document("all")
    doc = doc_ref.get()
    items = doc.to_dict().get("items", []) if doc.exists else []
    items.insert(0, record)
    doc_ref.set({"items": items})
    return {"ok": True}

@app.delete("/records/{uid}/{record_id}", summary="기록 삭제")
async def delete_record(uid: str, record_id: str):
    doc_ref = db.collection("users").document(uid).collection("records").document("all")
    doc = doc_ref.get()
    if doc.exists:
        items = [r for r in doc.to_dict().get("items", []) if str(r.get("id")) != record_id]
        doc_ref.set({"items": items})
    return {"ok": True}


class FeedbackRequest(BaseModel):
    uid: str
    rating: str                      # "up" | "down"
    user_message: str
    bot_response: str
    conversation_id: Optional[str] = None


@app.post("/feedback", summary="응답 피드백 저장")
async def submit_feedback(req: FeedbackRequest):
    try:
        fb_save_feedback(
            uid=req.uid,
            rating=req.rating,
            user_message=req.user_message,
            bot_response=req.bot_response,
            conversation_id=req.conversation_id or "",
        )
    except Exception as e:
        print(f"[Feedback] 저장 오류: {e}")
        raise HTTPException(status_code=500, detail="피드백 저장 실패")
    return {"ok": True}


@app.get("/cycle-info/{uid}", summary="자연임신 주기 정보 계산")
async def get_cycle_info(uid: str):
    """생리 기록 기반으로 주기, 배란 예정일, 가임기 계산"""
    from datetime import datetime, timedelta
    profile = fb_get_profile(uid)
    if not profile:
        raise HTTPException(404, "유저를 찾을 수 없습니다.")

    # 생리 기록 수집 (notes에서 [생리시작일] 태그)
    notes = fb_get_notes(uid) if 'fb_get_notes' in dir() else []
    try:
        from firebase_config import get_notes as fb_get_notes_fn
        notes = fb_get_notes_fn(uid)
    except:
        notes = []

    period_records = []
    for n in notes:
        content = n.get('content', '')
        if content.startswith('[생리시작일]'):
            date_str = content.replace('[생리시작일]', '').strip()
            try:
                period_records.append(datetime.strptime(date_str, '%Y-%m-%d'))
            except:
                pass
    period_records.sort()

    # 온보딩 데이터
    onboarding_cycle = int(profile.get('cycle')) if str(profile.get('cycle', '')).isdigit() else 28
    period_date_str = profile.get('periodDate', '')
    last_period = None
    if period_date_str:
        try:
            last_period = datetime.strptime(period_date_str, '%Y-%m-%d')
        except:
            pass

    # 주기 계산: 데이터 기반 or 온보딩 값
    if len(period_records) >= 2:
        # 평균 주기 계산
        cycles = []
        for i in range(1, len(period_records)):
            diff = (period_records[i] - period_records[i-1]).days
            if 20 <= diff <= 45:  # 합리적 범위
                cycles.append(diff)
        avg_cycle = round(sum(cycles) / len(cycles)) if cycles else onboarding_cycle
        last_period = period_records[-1]
        data_source = 'calculated'
    elif len(period_records) == 1:
        if last_period and last_period < period_records[0]:
            diff = (period_records[0] - last_period).days
            avg_cycle = diff if 20 <= diff <= 45 else onboarding_cycle
        else:
            avg_cycle = onboarding_cycle
        last_period = period_records[0]
        data_source = 'single_record'
    else:
        avg_cycle = onboarding_cycle if onboarding_cycle > 0 else 28
        data_source = 'onboarding'

    if not last_period:
        return {"error": "생리 시작일 정보가 없습니다.", "data_source": "none"}

    today = datetime.now()
    day_in_cycle = (today - last_period).days + 1
    ovulation_day = avg_cycle - 14
    days_to_ovulation = ovulation_day - day_in_cycle
    next_period = last_period + timedelta(days=avg_cycle)
    fertile_start = last_period + timedelta(days=ovulation_day - 3)
    fertile_end = last_period + timedelta(days=ovulation_day + 1)

    # 현재 단계
    if day_in_cycle <= 5:
        phase = '생리 기간'
    elif day_in_cycle <= ovulation_day - 3:
        phase = '배란 준비 중'
    elif day_in_cycle <= ovulation_day + 1:
        phase = '배란기 (가임기)'
    else:
        phase = '착상 대기 중'

    return {
        "avg_cycle": avg_cycle,
        "last_period": last_period.strftime('%Y-%m-%d'),
        "day_in_cycle": day_in_cycle,
        "ovulation_day": ovulation_day,
        "days_to_ovulation": days_to_ovulation,
        "next_period": next_period.strftime('%Y-%m-%d'),
        "fertile_start": fertile_start.strftime('%Y-%m-%d'),
        "fertile_end": fertile_end.strftime('%Y-%m-%d'),
        "phase": phase,
        "data_source": data_source,
        "record_count": len(period_records),
    }


# ── 사용자 행동 분석 (Analytics) ──

class AnalyticsRequest(BaseModel):
    events: list[dict]


@app.post("/analytics/events", summary="행동 분석 이벤트 수집")
async def collect_analytics(req: AnalyticsRequest):
    """프론트엔드에서 수집한 클릭/체류시간/스크롤 이벤트 배치 저장"""
    if not req.events:
        return {"ok": True, "count": 0}
    # 이벤트 최대 50개 제한
    events = req.events[:50]
    try:
        fb_save_analytics(events)
    except Exception as e:
        print(f"[Analytics] 저장 오류: {e}")
        raise HTTPException(status_code=500, detail="분석 이벤트 저장 실패")
    return {"ok": True, "count": len(events)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "lyle-chatbot"}


# ── 프론트엔드 정적 파일 서빙 ──
_static_dir = pathlib.Path(__file__).resolve().parent.parent / "static"
if _static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_static_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback — 모든 경로를 index.html로"""
        file_path = _static_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))
