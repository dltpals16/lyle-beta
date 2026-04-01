"""
알림톡 스케줄러 — 매분 실행하여 발송 조건 확인
"""
from datetime import datetime, timedelta
from firebase_admin import firestore
from services.alimtalk import send_alimtalk

# 타임라인 단계 → 템플릿 매핑
PHASE_TO_TEMPLATE = {
    "과배란 유도": "타임라인안내_과배란주기",
    "과배란 유도 시작": "타임라인안내_과배란주기",
    "난자 채취": "타임라인안내_난자채취후",
    "에스트로겐 복용": "타임라인안내_FET준비",
    "내막 모니터링": "타임라인안내_FET준비",
    "프로게스테론 전환": "타임라인안내_FET준비",
    "배아 이식": "타임라인안내_이식후",
}

# 발송 시간 (시:분)
SEND_TIMES = {
    "복약알림": None,  # 사용자 설정 시간
    "타임라인안내_과배란주기": (19, 0),
    "타임라인안내_난자채취후": (11, 0),
    "타임라인안내_FET준비": (11, 0),
    "타임라인안내_이식후": (19, 0),
    "가임기알림": (11, 0),
    "판정일대기": (19, 0),
    "검사일직전": (19, 0),
}


def _get_db():
    return firestore.client()


def _get_sent_key(uid: str, template: str, date_str: str) -> str:
    return f"{uid}_{template}_{date_str}"


def _already_sent(db, uid: str, template: str, date_str: str) -> bool:
    """이미 발송했는지 확인"""
    doc = db.collection("notification_log").document(_get_sent_key(uid, template, date_str)).get()
    return doc.exists


def _mark_sent(db, uid: str, template: str, date_str: str):
    """발송 기록 저장"""
    db.collection("notification_log").document(_get_sent_key(uid, template, date_str)).set({
        "uid": uid,
        "template": template,
        "date": date_str,
        "sent_at": datetime.now().isoformat(),
    })


def _calc_cycle_day(period_date_str: str) -> int:
    """생리 시작일 기준 오늘이 몇일차인지"""
    try:
        period = datetime.strptime(period_date_str, "%Y-%m-%d").date()
        return (datetime.now().date() - period).days + 1
    except:
        return -1


def _calc_ovulation_day(period_date_str: str, cycle: int = 28) -> datetime:
    """배란 예정일 계산"""
    try:
        period = datetime.strptime(period_date_str, "%Y-%m-%d").date()
        return period + timedelta(days=cycle - 14)
    except:
        return None


def _calc_judgment_day(period_date_str: str, stage: str, protocol: str) -> datetime:
    """임신 판정일 계산 (시술별)"""
    try:
        period = datetime.strptime(period_date_str, "%Y-%m-%d").date()
        if stage == "fet":
            return period + timedelta(days=31)
        elif stage == "ivf":
            if protocol == "long":
                return period + timedelta(days=30)
            else:
                return period + timedelta(days=30)
        elif stage == "iui":
            return period + timedelta(days=27)
        elif stage == "timing":
            return period + timedelta(days=28)
        return None
    except:
        return None


def check_and_send_notifications():
    """
    매분 호출되는 메인 함수.
    모든 유저를 순회하며 발송 조건 확인 후 알림톡 발송.
    """
    from datetime import timezone, timedelta
    import requests as _req
    try:
        my_ip = _req.get("https://api.ipify.org", timeout=5).text
        print(f"[스케줄러] 서버 outbound IP: {my_ip}")
    except:
        print("[스케줄러] IP 확인 실패")
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    today = now.date()
    today_str = today.strftime("%Y-%m-%d")
    current_hour = now.hour
    current_minute = now.minute

    db = _get_db()

    # 알림 동의한 유저 조회
    users = db.collection("users").stream()

    user_count = 0
    for user_doc in users:
        try:
            data = user_doc.to_dict()
            uid = user_doc.id
            nickname = data.get("displayName", "")
            phone = data.get("phone", "")
            user_count += 1
            mode = data.get("mode", "")
            stage = data.get("stage", "")
            protocol = data.get("protocol", "")
            period_date = data.get("periodDate", "")
            current_phase = data.get("current_phase", "")
            phase_changed_at = data.get("phase_changed_at", "")
            cycle = data.get("cycle", 28)
            notif = data.get("notification_settings", {})

            # 전화번호 없으면 스킵
            if not phone or not nickname:
                continue

            # guest 스킵
            if uid.startswith("guest_"):
                continue

            # cycle이 문자열이면 기본값
            if isinstance(cycle, str):
                try:
                    cycle = int(cycle)
                except:
                    cycle = 28

            # ── 1. 복약 알림 ──
            if notif.get("med_reminder_on"):
                reminders = data.get("medication_reminders", []) or notif.get("med_reminders", [])
                print(f"[스케줄러:복약] {uid}: reminders={reminders}, now={current_hour}:{current_minute}")
                for rem in reminders:
                    rem_name = rem.get("name", "")
                    rem_time = rem.get("time", "")  # "08:00" 형태
                    if rem_time:
                        try:
                            h, m = map(int, rem_time.split(":"))
                            print(f"[스케줄러:복약] {uid}: {rem_name} 설정={h}:{m}, 현재={current_hour}:{current_minute}, 매칭={current_hour == h and current_minute == m}")
                            if current_hour == h and current_minute == m:
                                if not _already_sent(db, uid, f"복약_{rem_name}", today_str):
                                    print(f"[스케줄러:복약] {uid}: {rem_name} 발송 시도!")
                                    send_alimtalk("복약알림", phone, nickname, med=rem_name)
                                    _mark_sent(db, uid, f"복약_{rem_name}", today_str)
                        except Exception as e:
                            print(f"[스케줄러:복약] {uid}: 에러 {e}")

            # ── 2. 메디컬 체크 (타임라인 기반) ──
            medical_check_on = notif.get("medical_check_on") or (isinstance(notif.get("timeline_health_check"), dict) and notif["timeline_health_check"].get("enabled"))
            if medical_check_on and mode == "medical" and period_date:
                # 2-1. 타임라인 단계 알림 (단계 변경 1일 후)
                if current_phase and phase_changed_at:
                    try:
                        changed_date = datetime.strptime(phase_changed_at, "%Y-%m-%d").date()
                        days_since_change = (today - changed_date).days
                    except:
                        days_since_change = -1
                    if days_since_change == 1:
                        template_name = PHASE_TO_TEMPLATE.get(current_phase)
                        if template_name:
                            send_time = SEND_TIMES.get(template_name, (19, 0))
                            if send_time and current_hour == send_time[0] and current_minute == send_time[1]:
                                if not _already_sent(db, uid, template_name, today_str):
                                    send_alimtalk(template_name, phone, nickname)
                                    _mark_sent(db, uid, template_name, today_str)

                # 2-2. 판정일 대기 (판정일 7일 전)
                judgment_day = _calc_judgment_day(period_date, stage, protocol)
                if judgment_day:
                    days_to_judgment = (judgment_day - today).days
                    if days_to_judgment == 7 and current_hour == 19 and current_minute == 0:
                        if not _already_sent(db, uid, "판정일대기", today_str):
                            send_alimtalk("판정일대기", phone, nickname)
                            _mark_sent(db, uid, "판정일대기", today_str)

                    # 2-3. 검사일 직전 (판정일 1일 전)
                    if days_to_judgment == 1 and current_hour == 19 and current_minute == 0:
                        if not _already_sent(db, uid, "검사일직전", today_str):
                            send_alimtalk("검사일직전", phone, nickname)
                            _mark_sent(db, uid, "검사일직전", today_str)

            # ── 3. 가임기 알림 ──
            if notif.get("fertile_alert_on") and period_date:
                # 자연임신 또는 타이밍법
                if mode == "natural" or stage == "timing":
                    ovulation_day = _calc_ovulation_day(period_date, cycle if isinstance(cycle, int) else 28)
                    if ovulation_day:
                        fertile_start = ovulation_day - timedelta(days=3)
                        if today == fertile_start and current_hour == 10 and current_minute == 0:
                            ovulation_str = ovulation_day.strftime("%m월 %d일")
                            if not _already_sent(db, uid, "가임기알림", today_str):
                                send_alimtalk("가임기알림", phone, nickname, ovulation_date=ovulation_str)
                                _mark_sent(db, uid, "가임기알림", today_str)

        except Exception as e:
            print(f"[스케줄러] 유저 {uid} 처리 오류: {e}")
            continue

    print(f"[스케줄러] {now.strftime('%H:%M')} 알림 체크 완료 (유저 {user_count}명 처리)")
# force rebuild
