"""
알리고 카카오 알림톡 발송 모듈
⚠️ message 내용은 검수 통과된 템플릿과 개행문자 포함 완전히 동일해야 합니다.
"""
import requests
import json
import os

ALIGO_API_KEY = os.getenv("ALIGO_API_KEY", "hag8vprp63ow2bga6sss7ci2qkf5mi65")
ALIGO_USER_ID = os.getenv("ALIGO_USER_ID", "dltpals16")
ALIGO_SENDER_KEY = os.getenv("ALIGO_SENDER_KEY", "5b3de8ff20df9eb20032b3eaf8f45b4cd1b0fc99")
ALIGO_SENDER = os.getenv("ALIGO_SENDER", "01057448655")

TOKEN_URL = "https://kakaoapi.aligo.in/akv10/token/create/30/s/"
SEND_URL = "https://kakaoapi.aligo.in/akv10/alimtalk/send/"

# 템플릿 정의 — 알리고 원본과 정확히 일치해야 함
TEMPLATES = {
    "복약알림": {
        "tpl_code": "UG_2523",
        "subtitle": "라일 복약 알림",
        "build_message": lambda nick, med: f"{nick}님, 오늘도 잊지 않고 챙겨주세요!\r\n하나하나 챙기는 오늘의 노력이 분명 의미 있을거예요.",
        "build_emtitle": lambda nick, med: f"{med} 복용 시간이에요",
    },
    "타임라인안내_과배란주기": {
        "tpl_code": "UG_2525",
        "subtitle": "라일 시술 타임라인 안내",
        "build_message": lambda nick, **kw: f"{nick}님, 과배란 주사를 시작하셨네요! \r\n이 시기에는 주사 부위 통증, 복부 팽만감, 두통 등이 나타날 수 있어요. 대부분 정상적인 반응으로 금방 호전되니 너무 걱정하지 마세요. \r\n궁금한 점이 있으면 라일에게 물어보세요!",
        "build_emtitle": lambda nick, **kw: "과배란 주기 안내",
    },
    "타임라인안내_난자채취후": {
        "tpl_code": "UG_2533",
        "subtitle": "라일 시술 타임라인 안내",
        "build_message": lambda nick, **kw: f"{nick}님, 채취 수고하셨어요! 이식 전까지 충분히 쉬어주시고, 소화가 잘 되는 따뜻한 음식을 드시는게 좋아요, 소량의 출혈이나 복부 불편감이 있을 수 있습니다. 그러나 혹시 심한 복통, 발열, 많은 출혈량이 동반된다면 병원에 바로 연락해주세요. 정말 고생 많으셨어요.",
        "build_emtitle": lambda nick, **kw: "난자 채취 후 안내",
    },
    "타임라인안내_FET준비": {
        "tpl_code": "UG_2534",
        "subtitle": "라일 시술 타임라인 안내",
        "build_message": lambda nick, **kw: f"{nick}님, 이식 준비가 시작됐어요!\r\n에스트로겐·프로게스테론은 정해진 시간에 규칙적으로 복용/투여해주세요. 두통, 메스꺼움, 어지러움 등이 나타날 수 있지만, 대부분 정상적인 반응이에요. \r\n이식까지 한 걸음씩! 잘 해오고 계세요.",
        "build_emtitle": lambda nick, **kw: "동결배아이식 준비 안내",
    },
    "타임라인안내_이식후": {
        "tpl_code": "UG_2540",
        "subtitle": "라일 시술 타임라인 안내",
        "build_message": lambda nick, **kw: f"{nick}님, 이식은 잘 마치셨나요?\r\n이식 후에는 어떤 점을 챙기면 좋은지, 어떤 증상이 있을 수 있는지 정리해둘게요. 편하실 때 라일에게 물어봐 주세요. \r\n너무너무 수고 많으셨어요. 이제 몸에게 맡겨주세요!",
        "build_emtitle": lambda nick, **kw: "배아 이식 후 안내",
    },
    "가임기알림": {
        "tpl_code": "UG_2546",
        "subtitle": "라일 가임기 안내",
        "build_message": lambda nick, ovulation_date="", **kw: f"{nick}님, 생리 주기 기준으로 오늘부터 가임기 기간이에요. 배란 예정일은 {ovulation_date} 이며, 가임기는 배란일 전 후 약 5일간 지속됩니다. 더 자세한 내용은 라일에서 확인해보세요!\r\n",
        "build_emtitle": lambda nick, **kw: "오늘부터 가임기가 시작돼요",
    },
    "판정일대기": {
        "tpl_code": "UG_2548",
        "subtitle": "라일 시술 타임라인 안내",
        "build_message": lambda nick, **kw: f"{nick}님, 검사일까지 기다리는 시간이 길게 느껴지시죠. 작은 변화 하나에도 마음이 오르내리는 시기인 거 알고 있어요. 너무 스트레스 받지 마시고, 최대한 편안하게 보내셨으면 좋겠어요.\r\n사소한 궁금증이든, 감정적으로 힘든 순간이든 라일에게 언제든지 편하게 이야기해주세요!",
        "build_emtitle": lambda nick, **kw: "기다림의 시간",
    },
    "검사일직전": {
        "tpl_code": "UG_2550",
        "subtitle": "라일 시술 타임라인 안내",
        "build_message": lambda nick, **kw: f"{nick}님, 곧 검사일이에요.\r\n기대도, 불안도 크다는 것 알고 있어요. 혈액검사 결과를 확인하실 때까지, 마음 편히 보내셨으면 좋겠어요. 어떤 결과가 나오든, 여기까지 오신 것 정말 대단해요. \r\n언제나 응원합니다!",
        "build_emtitle": lambda nick, **kw: "검사일이 다가오고 있어요",
    },
}

BUTTON_INFO = json.dumps({
    "button": [
        {"name": "채널 추가", "linkType": "AC", "linkTypeName": "채널 추가"},
        {"name": "라일 바로가기", "linkType": "WL", "linkTypeName": "웹링크",
         "linkMo": "https://lyle-mvp.onrender.com/", "linkPc": "https://lyle-mvp.onrender.com/"},
    ]
})


def _get_token() -> str:
    """알리고 토큰 발급"""
    resp = requests.post(TOKEN_URL, data={
        "apikey": ALIGO_API_KEY,
        "userid": ALIGO_USER_ID,
    }, timeout=10)
    result = resp.json()
    token = result.get("token", "")
    if not token:
        print(f"[알림톡] 토큰 발급 실패: {result}")
    return token


def send_alimtalk(template_name: str, phone: str, nickname: str, **kwargs) -> dict:
    """
    알림톡 발송

    Args:
        template_name: TEMPLATES 키 (예: "복약알림", "타임라인안내_과배란주기")
        phone: 수신자 전화번호
        nickname: 사용자 닉네임
        **kwargs: 추가 변수 (med=약물명, ovulation_date=배란예정일 등)

    Returns:
        발송 결과 dict
    """
    tpl = TEMPLATES.get(template_name)
    if not tpl:
        print(f"[알림톡] 알 수 없는 템플릿: {template_name}")
        return {"code": -1, "message": f"Unknown template: {template_name}"}

    token = _get_token()
    if not token:
        return {"code": -1, "message": "Token creation failed"}

    # 복약알림은 med 파라미터 필요
    if template_name == "복약알림":
        message = tpl["build_message"](nickname, kwargs.get("med", ""))
        emtitle = tpl["build_emtitle"](nickname, kwargs.get("med", ""))
    else:
        message = tpl["build_message"](nickname, **kwargs)
        emtitle = tpl["build_emtitle"](nickname, **kwargs)

    # subject는 알리고 원본 subtitle 사용
    subject = tpl.get("subtitle", f"라일 {emtitle}")

    send_data = {
        "apikey": ALIGO_API_KEY,
        "userid": ALIGO_USER_ID,
        "token": token,
        "senderkey": ALIGO_SENDER_KEY,
        "tpl_code": tpl["tpl_code"],
        "sender": ALIGO_SENDER,
        "receiver_1": phone,
        "recvname_1": nickname,
        "subject_1": subject,
        "message_1": message,
        "emtitle_1": emtitle,
        "button_1": BUTTON_INFO,
        "testMode": "N",
    }

    try:
        resp = requests.post(SEND_URL, data=send_data, timeout=15)
        result = resp.json()
        success = result.get("code") == 0
        print(f"[알림톡] {'✅' if success else '❌'} {template_name} → {phone} ({nickname}): {result.get('message', '')}")
        return result
    except Exception as e:
        print(f"[알림톡] 발송 오류: {e}")
        return {"code": -1, "message": str(e)}
