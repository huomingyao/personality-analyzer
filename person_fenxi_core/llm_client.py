"""MiniMax LLM Client for Psyche KB."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator

import httpx
import numpy as np

from person_fenxi_core.config import get_minimax_api_key, get_minimax_model


@dataclass
class ChatMessage:
    """Chat message structure."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Chat completion response."""

    id: str
    content: str
    finish_reason: str | None
    usage: dict[str, int]


class MiniMaxClient:
    """MiniMax API client with retry and streaming support."""

    BASE_URL = "https://api.minimax.chat/v1"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 600.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key or get_minimax_api_key()
        self.model = model or get_minimax_model()
        self.timeout = timeout
        self.max_retries = max_retries

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_embedding(self, text: str) -> np.ndarray:
        """Get text embedding using MiniMax embedding API.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as numpy array

        Raises:
            httpx.HTTPStatusError: On API errors after retries
        """
        url = f"{self.BASE_URL}/text/embedding"

        payload = {
            "model": "embo01",
            "texts": [text],
        }

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        url,
                        json=payload,
                        headers=self._get_headers(),
                    )
                    response.raise_for_status()
                    data = response.json()

                    embeddings = data.get("data", [])
                    if not embeddings:
                        raise RuntimeError(f"No embedding returned: {data}")

                    return np.array(embeddings[0]["embedding"], dtype=np.float32)

            except httpx.HTTPStatusError:
                if attempt == self.max_retries - 1:
                    raise
                continue
            except httpx.ReadTimeout:
                if attempt == self.max_retries - 1:
                    raise
                continue

        raise RuntimeError("Max retries exceeded")

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        timeout: float | None = None,
    ) -> ChatResponse | Iterator[ChatResponse]:
        """Send chat completion request.

        Args:
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Enable streaming response
            timeout: Request timeout in seconds (overrides default)

        Returns:
            ChatResponse or iterator of ChatResponse for streaming
        """
        url = f"{self.BASE_URL}/text/chatcompletion_v2"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_chat(url, payload, timeout)

        return self._sync_chat(url, payload, timeout)

    def _sync_chat(self, url: str, payload: dict[str, Any], timeout: float | None = None) -> ChatResponse:
        """Synchronous chat completion."""
        effective_timeout = timeout if timeout is not None else self.timeout
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=effective_timeout) as client:
                    response = client.post(
                        url,
                        json=payload,
                        headers=self._get_headers(),
                    )
                    response.raise_for_status()
                    data = response.json()

                    choice = data["choices"][0]
                    return ChatResponse(
                        id=data.get("id", ""),
                        content=choice["message"]["content"],
                        finish_reason=choice.get("finish_reason"),
                        usage=data.get("usage", {}),
                    )

            except httpx.HTTPStatusError:
                if attempt == self.max_retries - 1:
                    raise
                continue
            except httpx.ReadTimeout:
                if attempt == self.max_retries - 1:
                    raise
                continue

        raise RuntimeError("Max retries exceeded")

    def _stream_chat(
        self,
        url: str,
        payload: dict[str, Any],
        timeout: float | None = None,
    ) -> Iterator[ChatResponse]:
        """Streaming chat completion."""
        effective_timeout = timeout if timeout is not None else self.timeout
        with httpx.Client(timeout=effective_timeout) as client:
            with client.stream(
                "POST",
                url,
                json=payload,
                headers=self._get_headers(),
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if not choices:
                        continue

                    delta = choices[0].get("delta", {})
                    yield ChatResponse(
                        id=data.get("id", ""),
                        content=delta.get("content", ""),
                        finish_reason=delta.get("finish_reason"),
                        usage={},
                    )


def get_embedding(text: str) -> np.ndarray:
    """Convenience function for getting text embedding."""
    client = MiniMaxClient()
    return client.get_embedding(text)


def chat_completion(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> ChatResponse:
    """Convenience function for chat completion."""
    client = MiniMaxClient()
    return client.chat_completion(messages, temperature, max_tokens)