"""Gemini provider — fallback #1 (priority=2). Also handles embedding."""

from collections.abc import AsyncIterator
from typing import Any

from app.config import settings
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)


def _to_gemini_history(
    messages: list[dict[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Map OpenAI-style messages → (system_instruction, gemini_contents).

    Gemini uses ``system_instruction`` separately from the conversation
    array, and only knows ``user`` and ``model`` roles.
    """
    system: str | None = None
    contents: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        text = msg.get("content") or ""
        if role == "system":
            system = (system + "\n" + text) if system else text
            continue
        gemini_role = "user" if role == "user" else "model"
        contents.append({"role": gemini_role, "parts": [{"text": text}]})
    return system, contents


@ProviderRegistry.register
class GeminiProvider(LLMProvider):
    name = "gemini"
    priority = 2

    def __init__(self) -> None:
        self.model = settings.gemini_model
        self.last_stream_usage: dict[str, Any] = {}

    async def is_available(self) -> bool:
        return bool(settings.gemini_api_key)

    def _build_payload(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> dict[str, Any]:
        system, contents = _to_gemini_history(messages)
        gen_cfg: dict[str, Any] = {}
        if "max_tokens" in kwargs:
            gen_cfg["maxOutputTokens"] = kwargs.pop("max_tokens")
        if "temperature" in kwargs:
            gen_cfg["temperature"] = kwargs.pop("temperature")
        # gemini-2.5-* charges thinking against the output token budget by
        # default; disable it explicitly so callers asking for short
        # answers actually receive text instead of empty content.
        gen_cfg.setdefault("thinkingConfig", {"thinkingBudget": 0})
        payload: dict[str, Any] = {"contents": contents}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        if gen_cfg:
            payload["generationConfig"] = gen_cfg
        return payload

    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> LLMResponse:
        import httpx

        kwargs.pop("model_override", None)  # Gemini ignores per-call override
        kwargs.pop("response_format", None)
        payload = self._build_payload(messages, **kwargs)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={settings.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = ""
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")

        usage_meta = data.get("usageMetadata", {}) or {}
        usage = {
            "prompt_tokens": usage_meta.get("promptTokenCount", 0),
            "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
            "total_tokens": usage_meta.get("totalTokenCount", 0),
        }
        return LLMResponse(content=text, provider=self.name, usage=usage)

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        import httpx

        self.last_stream_usage = {}
        kwargs.pop("model_override", None)
        kwargs.pop("response_format", None)
        payload = self._build_payload(messages, **kwargs)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:streamGenerateContent?alt=sse&key={settings.gemini_api_key}"
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk_text = line[len("data:") :].strip()
                    if not chunk_text:
                        continue
                    import json as _json

                    try:
                        data = _json.loads(chunk_text)
                    except _json.JSONDecodeError:
                        continue
                    for cand in data.get("candidates", []):
                        for part in cand.get("content", {}).get("parts", []):
                            piece = part.get("text", "")
                            if piece:
                                yield piece
                    if (usage_meta := data.get("usageMetadata")) is not None:
                        self.last_stream_usage = {
                            "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                            "completion_tokens": usage_meta.get(
                                "candidatesTokenCount", 0
                            ),
                            "total_tokens": usage_meta.get("totalTokenCount", 0),
                        }
