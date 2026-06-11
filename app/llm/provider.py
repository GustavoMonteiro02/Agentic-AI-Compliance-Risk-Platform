import json
from dataclasses import dataclass
import time
from typing import Any

import requests

from app.config import get_settings


@dataclass(frozen=True)
class LLMResult:
    content: str
    metadata: dict[str, Any]


class OptionalLLMProvider:
    """Small optional OpenAI adapter.

    The deterministic workflow remains the default. This adapter only runs when
    `AI_GENERATION_MODE=openai` and `OPENAI_API_KEY` are configured.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def enabled(self) -> bool:
        return self.settings.ai_generation_mode == "openai" and bool(self.settings.openai_api_key)

    def _metadata(
        self,
        started_at: float,
        response_data: dict[str, Any] | None = None,
        attempts: int = 1,
    ) -> dict[str, Any]:
        usage = (response_data or {}).get("usage", {})
        return {
            "provider": "openai",
            "model": self.settings.openai_model,
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "attempts": attempts,
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

    def _chat_completion(self, payload: dict[str, Any], timeout: int) -> tuple[dict[str, Any], int]:
        attempts = 0
        last_error: requests.RequestException | None = None
        max_attempts = max(1, self.settings.openai_max_retries + 1)
        url = f"{self.settings.openai_base_url.rstrip('/')}/chat/completions"
        for attempt in range(1, max_attempts + 1):
            attempts = attempt
            try:
                response = requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json(), attempts
            except requests.RequestException as exc:
                last_error = exc
                if attempt == max_attempts:
                    raise
        raise RuntimeError(f"OpenAI request failed after {attempts} attempts: {last_error}")

    def advisory_completion_result(self, system_prompt: str, user_prompt: str) -> LLMResult | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        data, attempts = self._chat_completion(
            {
                "model": self.settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": self.settings.openai_max_tokens,
            },
            timeout=self.settings.openai_timeout_seconds,
        )
        return LLMResult(
            content=data["choices"][0]["message"]["content"],
            metadata=self._metadata(started_at, data, attempts),
        )

    def advisory_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        result = self.advisory_completion_result(system_prompt, user_prompt)
        return result.content if result else None

    def structured_json_result(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        data, attempts = self._chat_completion(
            {
                "model": self.settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "max_tokens": self.settings.openai_max_tokens,
            },
            timeout=self.settings.openai_timeout_seconds,
        )
        content = data["choices"][0]["message"]["content"]
        return json.loads(content), self._metadata(started_at, data, attempts)

    def structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        result = self.structured_json_result(system_prompt, user_prompt)
        return result[0] if result else None
