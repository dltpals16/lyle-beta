"""
Firebase Admin SDK 연동
Firestore를 통한 사용자 프로필, 채팅 히스토리 영구 저장
"""
import os
import json
import base64
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CREDENTIAL_PATH

# Render 환경에서 cryptography의 RSA 키 로딩 실패 우회: 순수 Python RSA 백엔드 강제 사용
try:
    from google.auth.crypt import _python_rsa
    import google.auth.crypt as _crypt_pkg
    import google.auth.crypt.rsa as _crypt_rsa
    # 모든 참조 지점에서 RSASigner를 순수 Python 구현으로 교체
    _crypt_pkg.RSASigner = _python_rsa.RSASigner
    _crypt_rsa.RSASigner = _python_rsa.RSASigner
    # _cryptography_rsa 모듈도 직접 패치
    try:
        from google.auth.crypt import _cryptography_rsa
        _cryptography_rsa.RSASigner = _python_rsa.RSASigner
    except ImportError:
        pass
    print("[Firebase] Forced pure-Python RSA backend (all refs patched)")
except Exception as e:
    print(f"[Firebase] RSA backend patch skipped: {e}")

# Firebase 초기화 — 환경변수 우선 사용 (Base64 > JSON > 로컬 파일)
_firebase_b64 = os.environ.get("FIREBASE_CREDENTIALS_BASE64")
_firebase_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

if _firebase_b64:
    cred_dict = json.loads(base64.b64decode(_firebase_b64).decode())
    cred = credentials.Certificate(cred_dict)
    print("[Firebase] Initialized from Base64 env")
elif _firebase_json:
    cred_dict = json.loads(_firebase_json)
    if "private_key" in cred_dict:
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(cred_dict)
    print("[Firebase] Initialized from JSON env")
else:
    cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)

firebase_admin.initialize_app(cred)
db = firestore.client()

print("[Firebase] Firestore 연결 완료")


# ==================== 프로필 ====================

def get_user_profile(uid: str) -> Optional[dict]:
    """Firestore에서 사용자 프로필 조회"""
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def save_user_profile(uid: str, data: dict):
    """Firestore에 사용자 프로필 저장 (merge)"""
    db.collection("users").document(uid).set(data, merge=True)


def update_user_profile(uid: str, updates: dict):
    """Firestore 프로필 부분 업데이트 (대화 중 자동 감지된 변경)"""
    if not updates:
        return
    ref = db.collection("users").document(uid)
    if ref.get().exists:
        ref.update(updates)


# ==================== 채팅 히스토리 ====================

def save_chat_messages(uid: str, messages: list[dict], conversation_id: str = None):
    """채팅 메시지 저장 (대화별)"""
    if not conversation_id:
        conversation_id = "latest"
    ref = db.collection("users").document(uid).collection("conversations").document(conversation_id)
    ref.set({
        "messages": messages,
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }, merge=True)


def update_conversation_title(uid: str, conversation_id: str, title: str):
    """대화 제목 업데이트"""
    ref = db.collection("users").document(uid).collection("conversations").document(conversation_id)
    ref.set({"title": title}, merge=True)


def get_chat_messages(uid: str, conversation_id: str = None) -> list[dict]:
    """채팅 메시지 불러오기"""
    if not conversation_id:
        conversation_id = "latest"
    doc = db.collection("users").document(uid).collection("conversations").document(conversation_id).get()
    if doc.exists:
        return doc.to_dict().get("messages", [])
    return []


def list_conversations(uid: str) -> list[dict]:
    """사용자의 모든 대화 목록 조회 (최신순)"""
    docs = (
        db.collection("users").document(uid).collection("conversations")
        .order_by("updatedAt", direction=firestore.Query.DESCENDING)
        .stream()
    )
    result = []
    for doc in docs:
        data = doc.to_dict()
        msgs = data.get("messages", [])
        # 첫 번째 사용자 메시지를 미리보기로
        preview = ""
        for m in msgs:
            if m.get("role") == "user":
                preview = m.get("content", "")[:50]
                break
        result.append({
            "id": doc.id,
            "title": data.get("title", ""),
            "preview": preview,
            "messageCount": len([m for m in msgs if m.get("role") == "user"]),
            "updatedAt": data.get("updatedAt"),
            "starred": data.get("starred", False),
        })
    return result


def star_conversation(uid: str, conversation_id: str, starred: bool):
    """대화 즐겨찾기 토글"""
    ref = db.collection("users").document(uid).collection("conversations").document(conversation_id)
    ref.set({"starred": starred}, merge=True)


def rename_conversation(uid: str, conversation_id: str, title: str):
    """대화 이름 변경"""
    ref = db.collection("users").document(uid).collection("conversations").document(conversation_id)
    ref.set({"title": title}, merge=True)


def delete_conversation(uid: str, conversation_id: str):
    """대화 삭제"""
    db.collection("users").document(uid).collection("conversations").document(conversation_id).delete()


# ==================== 진료 질문 체크리스트 ====================

def _dq_ref(uid: str):
    """doctor_questions subcollection 참조"""
    return db.collection("users").document(uid).collection("doctor_questions")


# ── 문자열 기반 유사도 (경량) ──
def _is_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    """단순 문자열 포함/일치 기반 유사도 판단"""
    a_clean = a.strip().lower()
    b_clean = b.strip().lower()
    if a_clean == b_clean:
        return True
    if len(a_clean) > 5 and len(b_clean) > 5:
        if a_clean in b_clean or b_clean in a_clean:
            return True
    # 짧은 문자열은 키워드 겹침으로 판단
    a_set = set(a_clean.split())
    b_set = set(b_clean.split())
    if a_set and b_set:
        overlap = len(a_set & b_set) / max(len(a_set), len(b_set))
        return overlap >= threshold
    return False


def add_doctor_questions(uid: str, questions: list):
    """진료 질문 추가 (유사 중복 방지)"""
    import uuid
    from datetime import datetime

    ref = _dq_ref(uid)
    # 기존 질문 content 목록 (중복 체크용)
    existing_contents = []
    for doc in ref.stream():
        data = doc.to_dict()
        existing_contents.append(data.get("content", ""))

    added = []
    for q_text in questions:
        if not q_text or not q_text.strip():
            continue
        q_clean = q_text.strip()
        # exact match 또는 유사도 높은 기존 질문이 있으면 스킵
        if any(q_clean == ex or _is_similar(q_clean, ex) for ex in existing_contents):
            print(f"  [Firestore] 진료 질문 중복 스킵: {q_clean}")
            continue
        doc_id = str(uuid.uuid4())[:8]
        item = {
            "id": doc_id,
            "content": q_clean,
            "checked": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "followed_up": False,
        }
        ref.document(doc_id).set(item)
        added.append(item)
        existing_contents.append(q_clean)
        print(f"  [Firestore] 진료 질문 추가: {q_clean}")

    return added


def get_doctor_questions(uid: str, only_pending: bool = False) -> list:
    """진료 질문 목록 조회"""
    ref = _dq_ref(uid)
    results = []
    for doc in ref.order_by("created_at").stream():
        data = doc.to_dict()
        if only_pending and data.get("checked", False):
            continue
        results.append(data)
    return results


def check_doctor_question(uid: str, question_id: str) -> Optional[dict]:
    """진료 질문 체크 (완료 처리)"""
    from datetime import datetime

    ref = _dq_ref(uid).document(question_id)
    doc = ref.get()
    if not doc.exists:
        return None
    ref.update({
        "checked": True,
        "completed_at": datetime.now().isoformat(),
    })
    return ref.get().to_dict()


def uncheck_doctor_question(uid: str, question_id: str) -> Optional[dict]:
    """진료 질문 체크 해제"""
    ref = _dq_ref(uid).document(question_id)
    doc = ref.get()
    if not doc.exists:
        return None
    ref.update({
        "checked": False,
        "completed_at": None,
    })
    return ref.get().to_dict()


def delete_doctor_question(uid: str, question_id: str):
    """진료 질문 삭제"""
    _dq_ref(uid).document(question_id).delete()


def get_completed_not_followed_up(uid: str) -> list:
    """체크됐지만 아직 후속 질문 안 한 진료 질문 조회"""
    ref = _dq_ref(uid)
    results = []
    for doc in ref.stream():
        data = doc.to_dict()
        if data.get("checked") and not data.get("followed_up"):
            results.append(data)
    return results


def mark_followed_up(uid: str, question_id: str):
    """후속 질문 완료 마킹"""
    ref = _dq_ref(uid).document(question_id)
    if ref.get().exists:
        ref.update({"followed_up": True})


# ==================== 채팅 기억 (Notes) ====================

def save_notes(uid: str, notes: list[dict]):
    """채팅 기억 저장 (전체 덮어쓰기)"""
    ref = db.collection("users").document(uid)
    ref.set({"chatMemory": notes}, merge=True)


def get_notes(uid: str) -> list[dict]:
    """채팅 기억 조회"""
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict().get("chatMemory", [])
    return []


def delete_note(uid: str, note_id: str) -> bool:
    """채팅 기억 개별 삭제"""
    doc_ref = db.collection("users").document(uid)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    notes = doc.to_dict().get("chatMemory", [])
    updated = [n for n in notes if n.get("id") != note_id]
    if len(updated) == len(notes):
        return False
    doc_ref.update({"chatMemory": updated})
    return True


# ==================== 피드백 ====================

def save_feedback(uid: str, rating: str, user_message: str, bot_response: str, conversation_id: str):
    """👍/👎 피드백 저장 (feedback 컬렉션)"""
    db.collection("feedback").add({
        "uid": uid,
        "rating": rating,           # "up" | "down"
        "user_message": user_message,
        "bot_response": bot_response,
        "conversation_id": conversation_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
    })


# ==================== 사용자 행동 분석 (Analytics) ====================

def save_analytics_events(events: list[dict]):
    """행동 분석 이벤트 배치 저장 (analytics 컬렉션)"""
    batch = db.batch()
    col_ref = db.collection("analytics")
    for event in events:
        event["serverTimestamp"] = firestore.SERVER_TIMESTAMP
        doc_ref = col_ref.document()
        batch.set(doc_ref, event)
    batch.commit()
