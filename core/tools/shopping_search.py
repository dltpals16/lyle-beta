"""
헬스케어 상품 검색 Tool
네이버 쇼핑 API로 화이트리스트 mall(쿠팡/롯데온/올리브영/약국몰 등)의 상품을 검색.
"""
import os
import re
import requests
from dataclasses import dataclass, field
from typing import Optional


# 화이트리스트 쇼핑몰 (mallName 부분 매칭)
# 카테고리 무관하게 신뢰성 있는 종합 + 헬스/영양 전문몰
TRUSTED_MALLS = [
    "쿠팡",
    "롯데온",
    "롯데ON",
    "GS SHOP",
    "GS shop",
    "올리브영",
    "약국몰",
    "약사몰",
    "마켓컬리",
    "CJ온스타일",
    "11번가",
    "이마트몰",
    "SSG",
    "신세계몰",
]

# 정렬 옵션
SORT_SIM = "sim"      # 유사도순 (기본)
SORT_DATE = "date"    # 날짜순 (신상)
SORT_ASC = "asc"      # 가격 오름차순
SORT_DSC = "dsc"      # 가격 내림차순


@dataclass
class Product:
    title: str
    link: str
    image: Optional[str]
    lprice: Optional[str]                  # 최저가 (문자열, 원 단위 숫자만)
    hprice: Optional[str] = None
    mall_name: Optional[str] = None
    product_id: Optional[str] = None
    category1: Optional[str] = None        # 패션의류/식품/...
    category2: Optional[str] = None
    category3: Optional[str] = None
    category4: Optional[str] = None
    brand: Optional[str] = None
    maker: Optional[str] = None

    def display_price(self) -> str:
        if not self.lprice:
            return "가격정보 없음"
        try:
            return f"{int(self.lprice):,}원"
        except Exception:
            return f"{self.lprice}원"


class ShoppingSearchTool:
    """헬스케어 제품 검색 (네이버 쇼핑 API + TRUSTED_MALLS 필터)"""

    def __init__(self):
        self.client_id = os.getenv("NAVER_CLIENT_ID", "")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
        self._headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
        }
        print("[ShoppingSearchTool] 초기화 완료")

    def search(
        self,
        query: str,
        display: int = 20,
        sort: str = SORT_SIM,
        trusted_only: bool = True,
        max_results: int = 8,
    ) -> list[Product]:
        """제품 검색.

        Args:
            query: 검색어 (예: "활성형 엽산", "전자체온계")
            display: 네이버 API에서 받을 후보 수 (max 100)
            sort: sim(유사도), date(최신), asc(저가), dsc(고가)
            trusted_only: True면 TRUSTED_MALLS만 통과
            max_results: 최종 반환 상한
        """
        if not self.client_id:
            print("  [ShoppingSearchTool] NAVER_CLIENT_ID 미설정")
            return []

        try:
            resp = requests.get(
                "https://openapi.naver.com/v1/search/shop.json",
                params={"query": query, "display": display, "sort": sort},
                headers=self._headers,
                timeout=6,
            )
            if resp.status_code != 200:
                print(f"  [ShoppingSearchTool] API 오류: {resp.status_code}")
                return []
        except Exception as e:
            print(f"  [ShoppingSearchTool] 호출 실패: {e}")
            return []

        raw_items = resp.json().get("items", [])

        # mall 필터 + 정규화
        products: list[Product] = []
        seen_pids: set = set()
        for it in raw_items:
            mall = it.get("mallName", "")

            if trusted_only and not _is_trusted_mall(mall):
                continue

            pid = it.get("productId") or it.get("link", "")
            if pid in seen_pids:
                continue
            seen_pids.add(pid)

            products.append(
                Product(
                    title=_strip_html(it.get("title", "")),
                    link=it.get("link", ""),
                    image=it.get("image"),
                    lprice=it.get("lprice"),
                    hprice=it.get("hprice"),
                    mall_name=mall,
                    product_id=pid,
                    category1=it.get("category1"),
                    category2=it.get("category2"),
                    category3=it.get("category3"),
                    category4=it.get("category4"),
                    brand=it.get("brand"),
                    maker=it.get("maker"),
                )
            )

            if len(products) >= max_results:
                break

        # trusted에서 결과가 너무 적으면 trusted_only=False로 fallback
        if trusted_only and len(products) < 3:
            fallback = self.search(
                query=query,
                display=display,
                sort=sort,
                trusted_only=False,
                max_results=max_results,
            )
            # trusted 우선 + 나머지 보충
            seen = {p.product_id for p in products}
            for p in fallback:
                if p.product_id not in seen and len(products) < max_results:
                    products.append(p)

        return products


# ─────────────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────────────

def _is_trusted_mall(mall_name: str) -> bool:
    """mallName이 TRUSTED_MALLS 중 하나를 포함하는지 (대소문자 무관, 부분 매칭)."""
    if not mall_name:
        return False
    m = mall_name.strip().lower()
    return any(t.lower() in m for t in TRUSTED_MALLS)


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()
