"""
LLM 클라이언트 — OpenAI 래퍼
메인 생성: Responses API (웹검색 지원)
경량 생성: Chat Completions API
"""
import os
from config import (
    OPENAI_MODEL_MAIN,
    OPENAI_MODEL_LIGHT,
    OPENAI_MAX_TOKENS,
    OPENAI_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_DIM,
)


class LLMClient:
    """LLM API 클라이언트 (OpenAI)"""

    def __init__(self):
        self._init_client()

    def _init_client(self):
        """OpenAI 클라이언트 초기화"""
        try:
            from openai import OpenAI
            self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except ImportError:
            self.openai = None
            print("[LLMClient] openai 패키지 없음. pip install openai")

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] = None,
        max_tokens: int = OPENAI_MAX_TOKENS,
        web_search: bool = False,
        model: str = None,
    ) -> str:
        """
        Responses API로 응답 생성 (메인/경량 모델 통합)
        model 미지정 시 메인 모델 사용
        """
        if not self.openai:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다.")

        # input 메시지 조립
        input_messages = []
        if history:
            for msg in history:
                input_messages.append({"role": msg["role"], "content": msg["content"]})
        input_messages.append({"role": "user", "content": user_message})

        # 도구 설정
        tools = []
        if web_search:
            tools.append({
                "type": "web_search_preview",
                "search_context_size": "medium",
            })

        kwargs = {
            "model": model or OPENAI_MODEL_MAIN,
            "instructions": system_prompt or None,
            "input": input_messages,
            "max_output_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.openai.responses.create(**kwargs)
        return response.output_text

    def generate_light(
        self,
        prompt: str,
        max_tokens: int = 100,
        history: list[dict] = None,
        system_prompt: str = None,
    ) -> str:
        """
        경량 모델로 생성 — Responses API 통합 래퍼
        """
        return self.generate(
            system_prompt=system_prompt or "",
            user_message=prompt,
            history=history,
            max_tokens=max_tokens,
            model=OPENAI_MODEL_LIGHT,
        )

    def embed(self, text: str) -> list[float]:
        """텍스트를 임베딩 벡터로 변환"""
        if not self.openai:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다.")

        response = self.openai.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """복수 텍스트 일괄 임베딩"""
        if not self.openai:
            raise RuntimeError("OpenAI 클라이언트가 초기화되지 않았습니다.")

        response = self.openai.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]
