"""
[Step 9] 프로필 자동 업데이트
mini 모델로 대화에서 저장할 정보를 추출합니다.
"""
import json
from models import UserProfile
from core.llm_client import LLMClient


class ProfileUpdater:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def extract(self, user_input: str, response_text: str, profile: UserProfile) -> dict:
        """mini 모델로 대화에서 저장할 정보 추출"""
        prompt = f"""아래 대화에서 사용자가 직접 보고한 구체적 사실이 있으면 JSON으로 추출하세요.

저장 대상: 약물/영양제 복용 보고, 시술 단계 변경 보고, 검사 수치 보고, 진단명 보고, 회차 변경, 프로토콜 변경, 배아 등급/개수, 지역, 혼인 상태, 동결배아 수
저장 제외: 질문만 한 경우, AI 답변 내용, 일시적 감정, 일상 대화, 추론, 약물/시술에 대한 정보 질문

⚠ current_phase 업데이트 조건 (매우 엄격):
- 사용자가 "오늘 채취했어", "이식 완료했어", "과배란 주사 시작했어", "트리거 맞았어" 등 본인의 시술 진행을 직접 보고한 경우에만 업데이트
- "고날에프랑 퓨레곤 차이가 뭐야?", "배아 등급이 뭐야?" 같은 정보 질문은 절대 current_phase를 변경하지 말 것
- 약물 이름을 언급했다고 해서 해당 단계로 업데이트하지 말 것. "~했어", "~받았어", "~시작했어" 같은 완료/시작 보고만 해당.

fields 키: treatment_stage(prep/testing/iui/ivf/fet/retry), treatment_cycle(숫자), current_phase(타임라인 단계명), protocol, amh, diagnoses, region1, region2, total_frozen_embryos
notes: fields에 안 맞는 사실 (예: "남편 정계정맥류", "이노시톨 복용중", "난자 10개 채취")

사용자 프로필: {profile.context_summary() if hasattr(profile, 'context_summary') else ''}

사용자 메시지: {user_input}
라일 응답: {response_text[:300]}

저장할 것이 없으면 빈 JSON {{}}을 반환하세요.
있으면 {{"fields": {{}}, "notes": []}} 형태로 반환하세요. 해당 없는 키는 생략.
JSON만 출력하세요."""

        try:
            raw = self.llm.generate_light(prompt, max_tokens=200)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return {}
            result = {}
            if parsed.get("fields"):
                result["fields"] = parsed["fields"]
            if parsed.get("notes"):
                result["notes"] = parsed["notes"]
            if result:
                print(f"  [ProfileUpdater] 프로필 업데이트 감지: {result}")
            return result
        except Exception as e:
            print(f"  [ProfileUpdater] 추출 실패: {e}")
            return {}
