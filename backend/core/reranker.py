"""
[Step 5] 리랭킹
검색 결과를 LLM으로 재정렬하여 가장 관련 있는 Top-N을 선별합니다.
"""
from config import RERANK_TOP_N
from models import RetrievedDocument
from prompts.templates import RERANKER
from core.llm_client import LLMClient


class Reranker:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def rerank(
        self,
        query: str,
        user_context: str,
        documents: list[RetrievedDocument],
        top_n: int = RERANK_TOP_N,
    ) -> list[RetrievedDocument]:
        """
        LLM으로 검색 결과를 재정렬합니다.

        1. 검색 결과를 번호와 함께 LLM에 전달
        2. LLM이 관련도 순으로 번호를 반환
        3. 해당 순서로 정렬하여 Top-N 반환
        """
        if not documents:
            return []

        if len(documents) <= top_n:
            return documents

        # 문서 목록을 프롬프트용 텍스트로 변환
        doc_texts = []
        for i, doc in enumerate(documents, 1):
            source_label = self._get_source_label(doc.collection)
            # 너무 긴 내용은 잘라서 전달
            content = doc.content[:300] + "..." if len(doc.content) > 300 else doc.content
            doc_texts.append(f"[{i}] ({source_label}) {content}")

        documents_str = "\n\n".join(doc_texts)

        prompt = RERANKER.format(
            user_query=query,
            user_context=user_context,
            documents=documents_str,
            top_n=top_n,
        )

        response = self.llm.generate_light(prompt, max_tokens=50)

        # 응답 파싱 (예: "3,1,5,2" → [3, 1, 5, 2])
        try:
            indices = self._parse_indices(response, len(documents))
            reranked = [documents[i - 1] for i in indices[:top_n]]

            # blog 쿼터 보장: 검색 결과에 blog가 있는데 rerank에서 탈락했으면 1개 보존
            blog_candidates = [d for d in documents if d.collection == "blog"]
            has_blog = any(d.collection == "blog" for d in reranked)
            if blog_candidates and not has_blog and len(reranked) >= top_n:
                best_blog = max(blog_candidates, key=lambda d: d.score)
                reranked[-1] = best_blog  # 마지막 자리에 blog 삽입

            return reranked
        except Exception:
            # 파싱 실패 시 원본 상위 N개 반환
            return documents[:top_n]

    def _parse_indices(self, response: str, max_idx: int) -> list[int]:
        """LLM 응답에서 문서 인덱스를 파싱"""
        # 숫자만 추출
        import re
        numbers = re.findall(r'\d+', response)
        indices = []
        for n in numbers:
            idx = int(n)
            if 1 <= idx <= max_idx and idx not in indices:
                indices.append(idx)
        return indices

    def _get_source_label(self, collection: str) -> str:
        labels = {
            "pdf_qna": "가이드북 Q&A",
            "pdf_chunk": "가이드북",
            "youtube_qna": "전문가 영상",
            "blog": "경험담",
            "web_reference": "의학 참고자료",
            "policy_chunk": "정책/지원사업",
        }
        return labels.get(collection, collection)
