"""
[Step 4] 벡터 검색
의도별 가중치에 따라 여러 컬렉션에서 검색합니다.
사용자 정보는 리랭킹/응답 생성 단계에서만 활용합니다.
"""
from qdrant_client import QdrantClient

import os
from config import (
    QDRANT_PATH,
    QDRANT_COLLECTIONS,
    RETRIEVAL_TOP_K,
    SIMILARITY_THRESHOLD,
    INTENT_COLLECTION_WEIGHTS,
)
from models import RetrievedDocument, UserProfile
from core.llm_client import LLMClient


class Retriever:
    def __init__(self, llm: LLMClient, qdrant_path: str = QDRANT_PATH):
        self.llm = llm
        qdrant_url = os.environ.get("QDRANT_URL")
        qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        try:
            if qdrant_url and qdrant_api_key:
                self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=30)
                print(f"[Retriever] Qdrant Cloud 모드 연결: {qdrant_url}")
            else:
                self.client = QdrantClient(path=qdrant_path)
                print(f"[Retriever] Qdrant 로컬 모드 연결: {qdrant_path}")
        except Exception as e:
            print(f"[Retriever] Qdrant 연결 실패: {e}")
            self.client = None

    def search(
        self,
        query: str,
        intent: str,
        profile: UserProfile,
        top_k: int = RETRIEVAL_TOP_K,
    ) -> list[RetrievedDocument]:
        """
        의도별 가중치에 따라 여러 컬렉션에서 검색합니다.

        1. 쿼리를 임베딩
        2. 의도에 따라 컬렉션별 검색 수 배분
        3. 결과 통합 및 유사도 임계값 필터링
        """
        if not self.client:
            return []

        # 쿼리 임베딩
        query_vector = self.llm.embed(query)

        # 의도별 가중치 가져오기
        weights = INTENT_COLLECTION_WEIGHTS.get(intent, INTENT_COLLECTION_WEIGHTS["medical"])

        # 가중치 총합으로 비율 계산
        total_weight = sum(weights.values())
        if total_weight == 0:
            return []

        all_results: list[RetrievedDocument] = []

        for collection_name, weight in weights.items():
            if weight == 0:
                continue

            # 비례 배분 (최소 1개)
            coll_top_k = max(1, round(top_k * weight / total_weight))

            try:
                response = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=coll_top_k,
                    with_payload=True,
                )

                for hit in response.points:
                    if hit.score < SIMILARITY_THRESHOLD:
                        continue

                    doc = self._parse_hit(hit, collection_name)
                    all_results.append(doc)

            except Exception as e:
                print(f"[Retriever] {collection_name} 검색 오류: {e}")
                continue

        # 유사도 점수 기준 정렬
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results

    def _parse_hit(self, hit, collection_name: str) -> RetrievedDocument:
        """Qdrant 검색 결과를 RetrievedDocument로 변환"""
        payload = hit.payload or {}

        # 컬렉션별 content 추출
        if collection_name in ("pdf_qna", "youtube_qna"):
            content = f"Q: {payload.get('question', '')}\nA: {payload.get('answer', '')}"
        elif collection_name == "pdf_chunk":
            content = payload.get("text", payload.get("content", ""))
            title = payload.get("title", "")
            if title:
                content = f"[{title}]\n{content}"
        elif collection_name == "blog":
            content = payload.get("text", payload.get("content", ""))
            title = payload.get("title", "")
            if title:
                content = f"[경험담] {title}\n{content}"
        elif collection_name in ("web_reference", "policy_chunk"):
            content = payload.get("text", payload.get("content", ""))
            title = payload.get("title", "")
            prefix = "[정책]" if collection_name == "policy_chunk" else "[참고자료]"
            if title:
                content = f"{prefix} {title}\n{content}"
        else:
            content = str(payload)

        return RetrievedDocument(
            collection=collection_name,
            score=hit.score,
            content=content,
            source=payload.get("source", collection_name),
            stage_ids=payload.get("stage_ids", []),
            entity_ids=payload.get("entity_ids", []),
            metadata=payload,
        )
