"""
난임 지정병원 검색 Tool
HIRA 데이터 기반으로 지역/시술 종류별 병원 필터링
"""
import json
import os
from config import POLICY_DATA_DIR, POLICY_DATA_FILES


# 인접 시군구 매핑 (주요 도시만)
_NEARBY = {
    # 서울
    "마포구": ["서대문구", "용산구", "은평구", "영등포구"],
    "강남구": ["서초구", "송파구", "강동구"],
    "서초구": ["강남구", "동작구", "관악구"],
    "송파구": ["강남구", "강동구", "광진구"],
    "영등포구": ["마포구", "동작구", "구로구", "양천구"],
    "종로구": ["중구", "서대문구", "성북구"],
    "중구": ["종로구", "용산구", "성동구"],
    "강서구": ["양천구", "영등포구", "마포구"],
    "노원구": ["도봉구", "강북구", "중랑구"],
    "관악구": ["동작구", "서초구", "금천구"],
    # 경기
    "성남시": ["분당구", "수정구", "중원구", "용인시", "하남시", "광주시"],
    "수원시": ["화성시", "용인시", "오산시"],
    "고양시": ["파주시", "김포시"],
    "용인시": ["수원시", "성남시", "화성시"],
    "부천시": ["인천", "김포시", "광명시"],
}


class HospitalSearchTool:
    """난임 지정병원 검색"""

    def __init__(self):
        self.hospitals = self._load_data()
        print(f"[HospitalSearchTool] 초기화 완료 ({len(self.hospitals)}개 병원)")

    def _load_data(self) -> list[dict]:
        """HIRA 병원 데이터 로드"""
        path = os.path.join(POLICY_DATA_DIR, POLICY_DATA_FILES["hospitals"])
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("기관목록", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[HospitalSearchTool] 데이터 로드 실패: {e}")
            return []

    def search(
        self,
        region: str = "",
        treatment_type: str = "",
        include_nearby: bool = True,
    ) -> dict:
        """
        병원 검색.

        Args:
            region: 지역 ("마포구", "서울 마포구", "서울특별시 마포구" 등)
            treatment_type: "ivf" | "iui" | "" (전체)
            include_nearby: 인근 지역 포함 여부

        Returns:
            {
                "found": bool,
                "region": str,
                "hospitals": list[dict],      # 해당 지역
                "nearby_hospitals": list[dict], # 인근 지역
                "total_count": int,
            }
        """
        print(f"  [HospitalSearchTool] 검색: region={region}, type={treatment_type}")

        # 지역 파싱
        sido, sigungu = self._parse_region(region)

        # 시술 종류 필터
        def match_treatment(h):
            if not treatment_type:
                return True
            if treatment_type.lower() in ("ivf", "체외수정", "시험관"):
                return h.get("체외수정", False)
            if treatment_type.lower() in ("iui", "인공수정"):
                return h.get("인공수정", False)
            return True

        # 메인 지역 검색
        main_results = []
        for h in self.hospitals:
            if not match_treatment(h):
                continue
            if sigungu and sigungu in h.get("시군구", ""):
                main_results.append(h)
            elif sido and not sigungu and sido in h.get("시도", ""):
                main_results.append(h)

        # 인근 지역 검색
        nearby_results = []
        if include_nearby and sigungu:
            nearby_areas = _NEARBY.get(sigungu, [])
            for h in self.hospitals:
                if not match_treatment(h):
                    continue
                h_sigungu = h.get("시군구", "")
                if h_sigungu in nearby_areas and h not in main_results:
                    nearby_results.append(h)

        # 의사수 기준 정렬
        main_results.sort(key=lambda x: x.get("의사수", 0), reverse=True)
        nearby_results.sort(key=lambda x: x.get("의사수", 0), reverse=True)

        # 결과 포맷팅
        formatted_main = [self._format_hospital(h) for h in main_results[:10]]
        formatted_nearby = [self._format_hospital(h) for h in nearby_results[:5]]

        return {
            "found": len(main_results) > 0 or len(nearby_results) > 0,
            "region": region,
            "hospitals": formatted_main,
            "nearby_hospitals": formatted_nearby,
            "total_count": len(main_results) + len(nearby_results),
        }

    def _parse_region(self, region: str) -> tuple[str, str]:
        """지역 문자열 파싱 → (시도, 시군구)"""
        if not region:
            return "", ""

        parts = region.split()
        sido = ""
        sigungu = ""

        for part in parts:
            if any(s in part for s in ["시", "도"]) and any(s in part for s in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]):
                sido = part.replace("특별시", "").replace("광역시", "").replace("특별자치시", "").replace("특별자치도", "")
            elif any(s in part for s in ["구", "군", "시"]):
                sigungu = part

        # 단일 토큰인 경우
        if not sido and not sigungu:
            if any(s in region for s in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원"]):
                sido = region.replace("특별시", "").replace("광역시", "")
            else:
                sigungu = region

        return sido, sigungu

    def _format_hospital(self, h: dict) -> dict:
        """병원 정보를 깔끔하게 포맷팅"""
        return {
            "병원명": h.get("병원명", ""),
            "주소": h.get("주소", ""),
            "전화번호": h.get("전화번호", ""),
            "종별": h.get("종별", ""),
            "인공수정": h.get("인공수정", False),
            "체외수정": h.get("체외수정", False),
            "의사수": h.get("의사수", 0),
            "홈페이지": h.get("홈페이지", ""),
            "시군구": h.get("시군구", ""),
        }
