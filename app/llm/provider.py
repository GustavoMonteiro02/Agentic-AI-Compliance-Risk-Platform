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
    """Optional LLM adapter for production refinement.

    The deterministic workflow remains the default. This adapter only runs when
    LLM mode is enabled and the selected provider has credentials configured.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def provider_name(self) -> str:
        return (getattr(self.settings, "llm_provider", None) or "openai").lower()

    def enabled(self) -> bool:
        if self.settings.ai_generation_mode not in {"openai", "llm"}:
            return False
        if self.provider_name in {"openai", "openai_compatible"}:
            return bool(self.settings.openai_api_key)
        if self.provider_name == "anthropic":
            return bool(self.settings.anthropic_api_key)
        return False

    def model_name(self) -> str:
        if self.provider_name == "anthropic":
            return self.settings.anthropic_model
        return self.settings.openai_model

    def _metadata(
        self,
        started_at: float,
        response_data: dict[str, Any] | None = None,
        attempts: int = 1,
    ) -> dict[str, Any]:
        usage = (response_data or {}).get("usage", {})
        if self.provider_name == "anthropic":
            usage = {
                "prompt_tokens": usage.get("input_tokens"),
                "completion_tokens": usage.get("output_tokens"),
                "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
                if usage
                else None,
            }
        return {
            "provider": self.provider_name,
            "model": self.model_name(),
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

    def _anthropic_completion(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], int]:
        attempts = 0
        last_error: requests.RequestException | None = None
        max_attempts = max(1, self.settings.openai_max_retries + 1)
        payload = {
            "model": self.settings.anthropic_model,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": self.settings.openai_max_tokens,
            "temperature": 0.1,
        }
        for attempt in range(1, max_attempts + 1):
            attempts = attempt
            try:
                response = requests.post(
                    f"{self.settings.anthropic_base_url.rstrip('/')}/messages",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.settings.openai_timeout_seconds,
                )
                response.raise_for_status()
                return response.json(), attempts
            except requests.RequestException as exc:
                last_error = exc
                if attempt == max_attempts:
                    raise
        raise RuntimeError(f"Anthropic request failed after {attempts} attempts: {last_error}")

    def _content_from_response(self, data: dict[str, Any]) -> str:
        if self.provider_name == "anthropic":
            return "".join(
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text" or "text" in block
            )
        return data["choices"][0]["message"]["content"]

    def advisory_completion_result(self, system_prompt: str, user_prompt: str) -> LLMResult | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        if self.provider_name == "anthropic":
            data, attempts = self._anthropic_completion(system_prompt, user_prompt)
        else:
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
            content=self._content_from_response(data),
            metadata=self._metadata(started_at, data, attempts),
        )

    def advisory_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        result = self.advisory_completion_result(system_prompt, user_prompt)
        return result.content if result else None

    def structured_json_result(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        if self.provider_name == "anthropic":
            json_instruction = "\n\nReturn only a valid JSON object. Do not include markdown fences."
            data, attempts = self._anthropic_completion(system_prompt, user_prompt + json_instruction)
        else:
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
        content = self._content_from_response(data)
        return json.loads(content), self._metadata(started_at, data, attempts)

    def structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        result = self.structured_json_result(system_prompt, user_prompt)
        return result[0] if result else None
