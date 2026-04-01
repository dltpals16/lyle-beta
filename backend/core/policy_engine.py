"""
PolicyEngine — 구조화된 정책 데이터 조회 엔진

7가지 쿼리 타입에 대해 JSON 데이터에서 정확한 정보를 매칭합니다.
벡터 검색 전에 실행되어 정확한 수치/절차 정보를 제공합니다.
"""
import json
import os
from models import UserProfile
from config import POLICY_DATA_DIR, POLICY_DATA_FILES


QUERY_TYPE_CLASSIFY_PROMPT = """사용자의 정책/지원금 관련 질문을 아래 7가지 타입 중 하나로 분류하세요.
반드시 타입 라벨 하나만 출력하세요.

## 타입 목록

지원금액 — 시술비 지원금, 금액, 비용, 얼마 받는지
  예: "시험관 비용 얼마예요?", "지원금 얼마나 받아요?", "동결배아 이식 비용"

서류_절차 — 신청 방법, 필요 서류, 절차, 보건소
  예: "서류 뭐 준비해야 돼요?", "어떻게 신청해요?", "통지서 유효기간"

세액공제 — 연말정산, 소득공제, 세금 환급, 의료비 공제
  예: "세액공제 어떻게 받아요?", "연말정산에서 돌려받을 수 있나요?"

건보급여 — 건강보험 적용, 본인부담률, 급여횟수, 비급여
  예: "보험 적용돼요?", "본인부담 몇 퍼센트?", "급여 횟수 몇 번?"

지자체_추가 — 지역별 추가 지원, 시/도/구 지원
  예: "서울에서 추가 지원 있어요?", "우리 지역 혜택"

병원찾기 — 난임 병원, 의료기관 찾기, 위치
  예: "근처 난임 병원 어디있어요?", "체외수정 가능한 병원"

한방치료 — 한의원, 한약, 침, 뜸 관련
  예: "한방치료도 지원돼요?", "한의원 난임 치료"

## 사용자 질문
{message}

타입:"""


# 지역 별칭 매핑 (사용자 입력 → 매칭 가능한 변형들)
REGION_ALIASES = {
    "서울": ["서울특별시", "서울시", "서울"],
    "부산": ["부산광역시", "부산시", "부산"],
    "대구": ["대구광역시", "대구시", "대구"],
    "인천": ["인천광역시", "인천시", "인천"],
    "광주": ["광주광역시", "광주시", "광주"],
    "대전": ["대전광역시", "대전시", "대전"],
    "울산": ["울산광역시", "울산시", "울산"],
    "세종": ["세종특별자치시", "세종시", "세종"],
    "경기": ["경기도", "경기"],
    "강원": ["강원특별자치도", "강원도", "강원"],
    "충북": ["충청북도", "충북"],
    "충남": ["충청남도", "충남"],
    "전북": ["전북특별자치도", "전라북도", "전북"],
    "전남": ["전라남도", "전남"],
    "경북": ["경상북도", "경북"],
    "경남": ["경상남도", "경남"],
    "제주": ["제주특별자치도", "제주도", "제주"],
}

# 역방향 매핑도 생성 (예: "서울특별시" → ["서울특별시", "서울시", "서울"])
_REVERSE_REGION = {}
for _short, _aliases in REGION_ALIASES.items():
    for _alias in _aliases:
        _REVERSE_REGION[_alias] = _aliases
    _REVERSE_REGION[_short] = _aliases


class PolicyEngine:
    """구조화된 정책 데이터 매칭 엔진"""

    def __init__(self, llm=None):
        self.llm = llm
        self.data = {}
        self._load_all()
        print(f"[PolicyEngine] 초기화 완료 ({len(self.data)}개 데이터 로드)")

    def _load_all(self):
        """모든 정책 JSON 파일 로드"""
        for key, filename in POLICY_DATA_FILES.items():
            filepath = os.path.join(POLICY_DATA_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.data[key] = json.load(f)
            except FileNotFoundError:
                print(f"[PolicyEngine] 파일 없음: {filepath}")
            except json.JSONDecodeError as e:
                print(f"[PolicyEngine] JSON 파싱 오류: {filepath} - {e}")

    _VALID_TYPES = {"지원금액", "서류_절차", "세액공제", "건보급여", "지자체_추가", "병원찾기", "한방치료"}

    def classify_query_type(self, message: str) -> str:
        """LLM으로 쿼리 타입 분류 (gpt-4o-mini)"""
        if not self.llm:
            return "일반"

        prompt = QUERY_TYPE_CLASSIFY_PROMPT.format(message=message)
        response = self.llm.generate_light(prompt, max_tokens=20)
        result = response.strip()

        # 유효한 타입인지 확인
        if result in self._VALID_TYPES:
            return result

        # 부분 매칭 시도 (LLM이 설명을 덧붙인 경우)
        for valid in self._VALID_TYPES:
            if valid in result:
                return valid

        return "일반"

    def lookup(self, message: str, profile: UserProfile) -> dict:
        """
        메시지와 프로필 기반으로 구조화 데이터에서 정보 조회.
        Returns: {"query_type": str, "structured_context": str, "found": bool}
        """
        query_type = self.classify_query_type(message)
        handler = {
            "지원금액": self._handle_support_amount,
            "서류_절차": self._handle_application_flow,
            "세액공제": self._handle_tax_deduction,
            "건보급여": self._handle_nhi_coverage,
            "지자체_추가": self._handle_local_support,
            "병원찾기": self._handle_hospital_search,
            "한방치료": self._handle_herbal,
        }.get(query_type)

        if handler:
            context = handler(message, profile)
            return {
                "query_type": query_type,
                "structured_context": context,
                "found": bool(context),
            }

        return {"query_type": "일반", "structured_context": "", "found": False}

    # ── 핸들러들 ──

    def _handle_support_amount(self, message: str, profile: UserProfile) -> str:
        """지원금액 조회"""
        tables = self.data.get("tables", {})
        amount_table = tables.get("support_amount_2026", {})
        count_table = tables.get("treatment_count_2026", {})
        copay_table = tables.get("insurance_copay_2026", {})
        non_covered = tables.get("non_covered_limits_2026", {})
        validity = tables.get("validity_period_2026", {})

        lines = ["[2026년 난임부부 시술비 지원 기준]"]

        # 지원금액
        if amount_table.get("data"):
            lines.append("\n■ 시술별 최대 지원금액:")
            for treatment, info in amount_table["data"].items():
                lines.append(f"  - {treatment}: {info['최대금액_표시']} ({info['횟수']})")

        # 횟수
        if count_table.get("data"):
            total = count_table["data"].get("합계", {})
            lines.append(f"\n■ 지원횟수: 출산당 최대 {total.get('총_횟수', 25)}회")
            lines.append(f"  - 체외수정: {count_table['data'].get('체외수정', {}).get('구성', '')}")
            lines.append(f"  - 인공수정: {count_table['data'].get('인공수정', {}).get('총_횟수', 5)}회")

        # 본인부담률
        if copay_table.get("data"):
            lines.append(f"\n■ 본인부담률: {copay_table['data'].get('본인부담률', '30%')} (연령구분 폐지)")

        # 비급여 지원 한도
        if non_covered.get("data"):
            lines.append("\n■ 비급여 항목 지원 한도:")
            for item_name, item_info in non_covered["data"].items():
                note = f" ({item_info['비고']})" if item_info.get("비고") else ""
                lines.append(f"  - {item_name}: {item_info['최대금액_표시']}{note}")

        # 통지서 유효기간
        if validity.get("data"):
            lines.append(f"\n■ 지원결정통지서 유효기간: {validity['data'].get('변경후', '6개월')} (2026년 변경)")

        # 사용자 맞춤 (시술 회차가 있으면)
        if profile.treatment_cycle > 0:
            stage = profile.treatment_stage
            cycle = profile.treatment_cycle
            lines.append(f"\n■ 현재 상황 기준 ({stage} {cycle}회차):")
            if "인공수정" in stage:
                remaining = max(0, 5 - cycle)
                lines.append(f"  - 인공수정 잔여 횟수: 약 {remaining}회")
                lines.append(f"  - 회당 최대 지원: 30만원")
            else:
                remaining = max(0, 20 - cycle)
                lines.append(f"  - 체외수정 잔여 횟수: 약 {remaining}회")
                lines.append(f"  - 회당 최대 지원: 신선배아 110만원 / 동결배아 50만원")

        lines.append(f"\n출처: {amount_table.get('source', '2026년 모자보건사업 안내')}")

        # 지역 정보가 있으면 해당 지역 추가 지원사업도 함께 안내
        if profile.region:
            local_info = self._handle_local_support("", profile)
            if local_info:
                lines.append(f"\n{local_info}")

        return "\n".join(lines)

    def _handle_application_flow(self, message: str, profile: UserProfile) -> str:
        """서류/절차 안내"""
        flow = self.data.get("application_flow", {})
        if not flow:
            return ""

        lines = ["[난임부부 시술비 지원 신청 절차]"]

        # 필수 서류
        checklist = flow.get("제출서류_체크리스트", {})
        common = checklist.get("공통_필수", [])
        if common:
            lines.append("\n■ 공통 필수 서류:")
            for doc in common:
                note = f" ({doc['비고']})" if doc.get("비고") else ""
                lines.append(f"  - {doc['서류']}{note}")

        # 핵심 주의사항
        warnings = flow.get("핵심_주의사항", [])
        if warnings:
            lines.append("\n■ 핵심 주의사항:")
            for w in warnings:
                lines.append(f"  - {w['내용']}")

        # 지원 내용 요약
        support = flow.get("지원내용", {})
        if support:
            lines.append(f"\n■ 지원 범위: {support.get('지원범위', '')}")
            if support.get("이월"):
                lines.append(f"  - 이월: {support['이월']}")
            if support.get("세액공제_관계"):
                lines.append(f"  - 세액공제: {support['세액공제_관계']}")

        # 사실혼 안내
        if profile.marriage_status == "defacto":
            lines.append("\n■ 사실혼 신청 시 유의사항:")
            lines.append("  - 온라인(정부24/e-보건소) 신청 불가 → 보건소 방문 신청만 가능")
            lines.append("  - 추가 서류: 사실혼 관계 증빙서류 (주민등록등본, 사실혼관계확인서 등)")
            lines.append("  - 관할 보건소에서 서류 확인 후 지원 결정")

        return "\n".join(lines)

    def _handle_tax_deduction(self, message: str, profile: UserProfile) -> str:
        """세액공제 안내"""
        tax = self.data.get("tax_deduction", {})
        if not tax:
            return ""

        services = tax.get("서비스목록", [])
        lines = ["[난임시술 관련 세액공제 안내]"]

        for svc in services:
            lines.append(f"\n■ {svc['servNm']}")
            core = svc.get("핵심정보", {})
            for k, v in core.items():
                lines.append(f"  - {k}: {v}")

            warnings = svc.get("사용자_핵심_주의사항", [])
            if warnings:
                lines.append("  주의사항:")
                for w in warnings:
                    lines.append(f"    - {w['내용']}")

            guide = svc.get("안내_연결", {})
            if guide:
                for k, v in guide.items():
                    lines.append(f"  {k}: {v}")

        # 세액공제 최적화 전략
        strategies = tax.get("세액공제_최적화_전략", [])
        if strategies:
            lines.append("\n■ 세액공제 최적화 전략:")
            for s in strategies:
                lines.append(f"\n  【{s['전략명']}】")
                lines.append(f"  {s['설명']}")
                if s.get("예시"):
                    lines.append(f"  예시: {s['예시']}")
                if s.get("주의사항"):
                    lines.append(f"  주의: {s['주의사항']}")
                if s.get("신청방법"):
                    lines.append(f"  방법: {s['신청방법']}")

        return "\n".join(lines)

    def _handle_nhi_coverage(self, message: str, profile: UserProfile) -> str:
        """건강보험 급여 안내"""
        nhi = self.data.get("nhi_coverage", {})
        if not nhi:
            return ""

        current = nhi.get("현행기준_2024년11월이후", {})
        lines = ["[난임시술 건강보험 급여 안내 (2024.11~ 현행)]"]

        # 본인부담률
        copay = current.get("본인부담률", {})
        if copay:
            lines.append(f"\n■ 본인부담률: {copay.get('기본급여_횟수내', '30%')}")
            lines.append(f"  - {copay.get('주의사항', '')}")

        # 급여 횟수
        count = current.get("급여횟수", {})
        if count:
            lines.append(f"\n■ 급여횟수 ({count.get('기준단위', '출산당')})")
            lines.append(f"  - 체외수정: {count.get('체외수정', '20회')}")
            lines.append(f"  - 인공수정: {count.get('인공수정', '5회')}")
            lines.append(f"  - 합계: {count.get('합계', '최대 25회')}")
            if count.get("출산후_리셋"):
                lines.append(f"  - 출산 후: {count['출산후_리셋']}")

        # 횟수 차감 기준
        deduct = count.get("횟수_차감기준", {})
        if deduct:
            lines.append("\n■ 횟수 차감 기준:")
            for k, v in deduct.items():
                lines.append(f"  - {k}: {v}")

        # 비급여 항목
        non_covered = current.get("비급여_항목", [])
        if non_covered:
            lines.append("\n■ 비급여 항목 (100% 본인부담):")
            for item in non_covered[:5]:
                lines.append(f"  - {item}")

        return "\n".join(lines)

    def _handle_local_support(self, message: str, profile: UserProfile) -> str:
        """3계층 지원사업 조회: 국가사업 + 시/도 사업 + 구/군 사업"""
        services_data = self.data.get("services", {})
        bokjiro_data = self.data.get("bokjiro", {})

        region = profile.region
        is_defacto = profile.marriage_status == "defacto"

        lines = ["[지원사업 종합 안내]"]

        all_services = services_data.get("수집_서비스", [])

        # ── 1계층: 국가사업 (보건복지부) ──
        # "난임부부 시술비 지원"은 _handle_support_amount에서 상세 안내하므로 제외
        national_services = [
            svc for svc in all_services
            if svc.get("소관기관명", "") == "보건복지부"
            and "난임부부 시술비 지원" not in svc.get("서비스명", "")
        ]
        if national_services:
            lines.append("\n■ 국가 지원사업 (보건복지부):")
            for svc in national_services:
                self._append_service_detail(lines, svc, is_defacto)

        # 복지로 중앙부처 서비스 (국가사업과 중복되지 않는 것만)
        bokjiro_services = bokjiro_data.get("서비스목록", [])
        national_names = {svc.get("서비스명", "") for svc in national_services}
        bokjiro_unique = [
            svc for svc in bokjiro_services
            if svc.get("servNm", "") not in national_names
        ]
        if bokjiro_unique:
            lines.append("\n■ 기타 중앙부처 지원사업:")
            for svc in bokjiro_unique:
                lines.append(f"  - {svc['servNm']}")
                summary = svc.get("wlfareInfoOutlCn", "")
                if summary:
                    lines.append(f"    {summary[:100]}")

        if all_services and region:
            # ── 2계층: 시/도 사업 (예: 서울특별시) ──
            region_parts = region.split()
            sido = region_parts[0] if region_parts else ""
            sigungu = region_parts[1] if len(region_parts) > 1 else ""

            sido_services = []
            sigungu_services = []

            for svc in all_services:
                org = svc.get("소관기관명", "")
                name = svc.get("서비스명", "")
                # 국가사업은 이미 위에서 처리
                if org == "보건복지부":
                    continue

                # 소관기관에서 구/군 부분 추출 (예: "서울특별시 마포구" → "마포구")
                org_parts = org.split()
                org_sigungu = org_parts[1] if len(org_parts) > 1 else ""

                if sigungu and (sigungu in org or sigungu in name):
                    # 3계층: 구/군 레벨 (소관기관 또는 서비스명에 사용자의 구/군 포함)
                    sigungu_services.append(svc)
                elif sido and org_sigungu:
                    # 다른 구/군 사업 → 스킵 (예: "서울특별시 중구"는 마포구 사용자에게 불필요)
                    continue
                elif sido and (org == sido or self._match_region(org, sido)):
                    # 2계층: 시/도 레벨 (소관기관이 정확히 시/도인 경우, 예: "서울특별시")
                    sido_services.append(svc)
                elif sido and self._match_region(name, sido) and not org_sigungu:
                    # 서비스명에 시/도명 포함 (예: "서울시 난자동결 시술비 지원")
                    sido_services.append(svc)

            if sido_services:
                lines.append(f"\n■ {sido} 지원사업:")
                for svc in sido_services[:5]:
                    self._append_service_detail(lines, svc, is_defacto)

            # ── 3계층: 구/군 자체사업 (예: 마포구) ──
            if sigungu_services:
                lines.append(f"\n■ {sigungu} 자체 지원사업:")
                for svc in sigungu_services[:5]:
                    self._append_service_detail(lines, svc, is_defacto)

            if not sido_services and not sigungu_services:
                lines.append(f"\n※ '{region}' 지역 특화 서비스는 현재 데이터에 없습니다.")
                lines.append("  관할 보건소에 문의하시면 정확한 정보를 얻으실 수 있어요.")
        elif not region:
            lines.append("\n※ 지역 정보가 없어 전국 공통 사업만 안내합니다.")
            lines.append("  지역을 알려주시면 해당 지자체 추가 지원도 안내해드릴 수 있어요.")

        return "\n".join(lines)

    def _append_service_detail(self, lines: list, svc: dict, is_defacto: bool):
        """서비스 상세정보를 lines에 추가하는 헬퍼"""
        lines.append(f"\n  【{svc['서비스명']}】 ({svc.get('소관기관명', '')})")
        detail = svc.get("상세정보", {})
        if detail.get("지원대상"):
            lines.append(f"  지원대상: {detail['지원대상'][:200]}")
        if detail.get("지원내용"):
            lines.append(f"  지원내용: {detail['지원내용'][:200]}")
        if detail.get("신청방법"):
            raw_method = detail['신청방법'][:300]
            lines.append(f"  신청방법: {raw_method}")
            if is_defacto:
                lines.append(f"  ⚠ 사실혼의 경우 온라인 신청이 불가하며, 보건소 방문 신청만 가능합니다. (사실혼 관계 증빙서류 지참 필요)")
        if detail.get("신청기한"):
            lines.append(f"  신청기한: {detail['신청기한']}")
        if detail.get("온라인신청URL"):
            if is_defacto:
                lines.append(f"  온라인신청: {detail['온라인신청URL']} (※ 사실혼은 온라인 신청 불가 → 보건소 방문 필요. 참고용 링크)")
            else:
                lines.append(f"  온라인신청: {detail['온라인신청URL']}")

    def _handle_hospital_search(self, message: str, profile: UserProfile) -> str:
        """병원 찾기"""
        hospitals_data = self.data.get("hospitals", {})
        if not hospitals_data:
            return ""

        region = profile.region
        hospital_list = hospitals_data.get("기관목록", [])
        total = hospitals_data.get("총_기관수", len(hospital_list))

        lines = [f"[난임시술 지정 의료기관 안내 (전국 {total}개)]"]

        # 지역별 집계
        by_region = hospitals_data.get("시도별_집계", {})
        if by_region:
            lines.append("\n■ 시도별 기관 수:")
            for r, count in sorted(by_region.items()):
                marker = " ◀" if region and region in r else ""
                lines.append(f"  - {r}: {count}개{marker}")

        # 사용자 지역 병원 목록
        if region:
            matched = [
                h for h in hospital_list
                if self._match_region(h.get("시도", ""), region)
                or self._match_region(h.get("시군구", ""), region)
            ]
            if matched:
                lines.append(f"\n■ {region} 지역 병원 ({len(matched)}개):")
                for h in matched[:10]:
                    ivf_mark = "체외수정 가능" if h.get("체외수정") else "인공수정만"
                    lines.append(f"  - {h['병원명']} ({h.get('시군구', '')}) [{ivf_mark}] {h.get('전화번호', '')}")
                if len(matched) > 10:
                    lines.append(f"  ... 외 {len(matched) - 10}개")
            else:
                lines.append(f"\n※ '{region}'에 해당하는 병원을 찾지 못했습니다.")
                lines.append("  시/도 단위로 검색됩니다 (예: 서울, 경기, 부산)")
        else:
            lines.append("\n※ 지역 정보가 없어 전체 목록만 안내합니다.")
            lines.append("  지역을 알려주시면 가까운 병원을 안내해드릴 수 있어요.")

        return "\n".join(lines)

    def _match_region(self, text: str, region: str) -> bool:
        """지역 별칭을 고려한 매칭. region이 text에 포함되는지, 또는 text가 region에 포함되는지 확인."""
        if not region or not text:
            return False
        # 직접 포함 (양방향: "서울특별시 마포구" in text, 또는 text in "서울특별시 마포구")
        if region in text or text in region:
            return True
        # 별칭 확장: 사용자 region의 모든 별칭으로 시도
        # region을 공백으로 분할하여 각 파트도 시도 (예: "서울특별시 마포구" → ["서울특별시", "마포구"])
        region_parts = region.split()
        for part in region_parts:
            if part in text:
                return True
            aliases = _REVERSE_REGION.get(part, [])
            if any(alias in text for alias in aliases):
                return True
        aliases = _REVERSE_REGION.get(region, [])
        return any(alias in text for alias in aliases)

    def _handle_herbal(self, message: str, profile: UserProfile) -> str:
        """한방치료 지원사업 조회 (infertility_services_dataset.json 내 한방 서비스)"""
        services_data = self.data.get("services", {})
        all_services = services_data.get("수집_서비스", [])

        # 한방 관련 서비스 필터
        herbal_keywords = ["한방", "한의", "한약", "침", "뜸"]
        herbal_services = [
            svc for svc in all_services
            if any(kw in svc.get("서비스명", "") for kw in herbal_keywords)
        ]

        if not herbal_services:
            return ""

        region = profile.region
        lines = [f"[한방 난임치료 지원사업 안내 (전국 {len(herbal_services)}건)]"]

        if region:
            matched = [
                svc for svc in herbal_services
                if self._match_region(svc.get("서비스명", ""), region)
                or self._match_region(svc.get("소관기관명", ""), region)
            ]
            if matched:
                lines.append(f"\n■ {region} 지역 한방 난임 지원:")
                for svc in matched:
                    lines.append(f"  - {svc['서비스명']} ({svc.get('소관기관명', '')})")
                    purpose = svc.get("서비스목적요약", "")
                    if purpose:
                        lines.append(f"    {purpose[:120]}")
            else:
                lines.append(f"\n※ '{region}' 지역에 한방 난임 지원사업이 없습니다.")
                lines.append("  아래는 전국 한방 난임 지원 지역 목록이에요.")
        else:
            lines.append("\n※ 지역 정보가 없어 전국 목록을 안내합니다.")
            lines.append("  지역을 알려주시면 해당 지역 지원사업을 안내해드릴 수 있어요.")

        # 전국 목록 (지역 매칭 안 됐거나 지역 없을 때)
        if not region or not matched:
            lines.append(f"\n■ 전국 한방 난임 지원 지역 ({len(herbal_services)}곳):")
            for svc in herbal_services:
                org = svc.get("소관기관명", "")
                lines.append(f"  - {svc['서비스명']} ({org})")

        lines.append("\n※ 한방치료도 난임시술비 지원 대상에 포함될 수 있으며, 관할 보건소에서 확인해주세요.")
        return "\n".join(lines)
