"""
약물 정보 검색 Tool
네이버 검색 API로 약학정보원(health.kr) 페이지를 찾고, 상세 정보를 가져옴
"""
import os
import re
import requests
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    """HTML에서 텍스트만 추출"""
    def __init__(self):
        super().__init__()
        self.texts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self.texts.append(text)

    def get_text(self) -> str:
        return "\n".join(self.texts)


class DrugSearchTool:
    """약물 정보 검색 (네이버 API + health.kr)"""

    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        self._headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        self._http_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        print("[DrugSearchTool] 초기화 완료")

    def search(self, drug_name: str) -> dict:
        """
        약물명으로 검색하여 공식 정보를 반환.

        Returns:
            {
                "found": bool,
                "drug_name": str,
                "source_url": str,
                "summary": str,       # 네이버 검색 스니펫
                "detail": str,        # health.kr 페이지 상세 내용
                "source": "약학정보원 (health.kr)"
            }
        """
        print(f"  [DrugSearchTool] 검색: {drug_name}")

        # 1단계: 네이버 검색으로 health.kr URL 확보
        search_results = self._naver_search(drug_name)
        if not search_results:
            return {"found": False, "drug_name": drug_name, "summary": "", "detail": "", "source_url": ""}

        # 2단계: health.kr URL 필터링 (공식 사이트만)
        health_kr_results = [r for r in search_results if "health.kr" in r["link"]]

        if not health_kr_results:
            # health.kr 결과 없으면 검색 스니펫만 반환
            best = search_results[0]
            return {
                "found": True,
                "drug_name": drug_name,
                "source_url": best["link"],
                "summary": best["description"],
                "detail": "",
                "source": best["link"],
            }

        # 3단계: health.kr 상세 페이지 fetch
        # result_drug.asp (제품 상세) 우선, 없으면 result_take.asp (복약정보)
        target = None
        for r in health_kr_results:
            if "result_drug.asp" in r["link"]:
                target = r
                break
        if not target:
            for r in health_kr_results:
                if "result_take.asp" in r["link"]:
                    target = r
                    break
        if not target:
            target = health_kr_results[0]

        detail = self._fetch_drug_page(target["link"])

        return {
            "found": True,
            "drug_name": drug_name,
            "source_url": target["link"],
            "summary": target["description"],
            "detail": detail,
            "source": "약학정보원 (health.kr)",
        }

    def _naver_search(self, drug_name: str, display: int = 5) -> list[dict]:
        """네이버 웹문서 검색"""
        if not self.client_id:
            print("  [DrugSearchTool] NAVER_CLIENT_ID 미설정")
            return []

        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/webkr.json",
                params={"query": f"{drug_name} 약학정보원", "display": display},
                headers=self._headers,
                timeout=5,
            )
            if resp.status_code != 200:
                print(f"  [DrugSearchTool] 네이버 API 오류: {resp.status_code}")
                return []

            data = resp.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": re.sub(r"<[^>]+>", "", item["title"]),
                    "link": item["link"],
                    "description": re.sub(r"<[^>]+>", "", item["description"]),
                })
            return results

        except Exception as e:
            print(f"  [DrugSearchTool] 네이버 검색 오류: {e}")
            return []

    def _fetch_drug_page(self, url: str) -> str:
        """health.kr 페이지에서 약물 상세 정보 추출"""
        try:
            resp = requests.get(url, headers=self._http_headers, timeout=10)
            if resp.status_code != 200:
                return ""

            # HTML → 텍스트
            parser = _TextExtractor()
            parser.feed(resp.text)
            full_text = parser.get_text()

            # 핵심 섹션 추출
            extracted = self._extract_sections(full_text)
            return extracted

        except Exception as e:
            print(f"  [DrugSearchTool] 페이지 fetch 오류: {e}")
            return ""

    def _extract_sections(self, text: str) -> str:
        """전체 텍스트에서 약물 관련 핵심 섹션만 추출"""
        lines = text.split("\n")
        sections = []
        current_section = None
        buffer = []

        # 관심 키워드
        section_keywords = [
            "성분", "함량", "용법", "용량", "효능", "효과",
            "부작용", "이상반응", "주의사항", "금기", "상호작용",
            "보관", "저장", "급여", "복약", "투여",
            "전문", "일반", "제조", "제형", "ATC", "약효",
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 섹션 헤더 감지
            is_section = any(kw in line for kw in section_keywords) and len(line) < 50
            if is_section:
                if current_section and buffer:
                    sections.append(f"[{current_section}]\n" + "\n".join(buffer[:10]))
                current_section = line
                buffer = []
            elif current_section:
                buffer.append(line)

        # 마지막 섹션
        if current_section and buffer:
            sections.append(f"[{current_section}]\n" + "\n".join(buffer[:10]))

        result = "\n\n".join(sections)

        # 너무 길면 잘라내기 (LLM 컨텍스트 절약)
        if len(result) > 3000:
            result = result[:3000] + "\n...(이하 생략)"

        return result if result else "(상세 정보 추출 실패)"
