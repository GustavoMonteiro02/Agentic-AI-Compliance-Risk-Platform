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

    def _metadata(self, started_at: float, response_data: dict[str, Any] | None = None) -> dict[str, Any]:
        usage = (response_data or {}).get("usage", {})
        return {
            "provider": "openai",
            "model": self.settings.openai_model,
            "latency_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

    def advisory_completion_result(self, system_prompt: str, user_prompt: str) -> LLMResult | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return LLMResult(content=data["choices"][0]["message"]["content"], metadata=self._metadata(started_at, data))

    def advisory_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        result = self.advisory_completion_result(system_prompt, user_prompt)
        return result.content if result else None

    def structured_json_result(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content), self._metadata(started_at, data)

    def structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        result = self.structured_json_result(system_prompt, user_prompt)
        return result[0] if result else None
