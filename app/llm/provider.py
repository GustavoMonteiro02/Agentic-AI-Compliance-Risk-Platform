import json
from dataclasses import dataclass
import hashlib
import time
from typing import Any

import requests

from app.config import get_settings
from app.llm.runtime import get_llm_runtime_config


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
        self.runtime_config = get_llm_runtime_config()

    @property
    def ai_generation_mode(self) -> str:
        return (getattr(self.runtime_config, "ai_generation_mode", None) or self.settings.ai_generation_mode).lower()

    @property
    def provider_name(self) -> str:
        return (
            getattr(self.runtime_config, "llm_provider", None) or getattr(self.settings, "llm_provider", None) or "openai"
        ).lower()

    @property
    def timeout_seconds(self) -> int:
        return getattr(self.runtime_config, "timeout_seconds", None) or self.settings.openai_timeout_seconds

    @property
    def max_retries(self) -> int:
        value = getattr(self.runtime_config, "max_retries", None)
        return value if value is not None else self.settings.openai_max_retries

    @property
    def max_tokens(self) -> int:
        return getattr(self.runtime_config, "max_tokens", None) or self.settings.openai_max_tokens

    @property
    def temperature(self) -> float:
        value = getattr(self.runtime_config, "temperature", None)
        return value if value is not None else 0.1

    def enabled(self) -> bool:
        if self.ai_generation_mode not in {"openai", "llm"}:
            return False
        if self.provider_name in {"openai", "openai_compatible"}:
            return bool(self.settings.openai_api_key)
        if self.provider_name == "anthropic":
            return bool(self.settings.anthropic_api_key)
        return False

    def model_name(self) -> str:
        if getattr(self.runtime_config, "model", None):
            return self.runtime_config.model or ""
        if self.provider_name == "anthropic":
            return self.settings.anthropic_model
        return self.settings.openai_model

    def _metadata(
        self,
        started_at: float,
        response_data: dict[str, Any] | None = None,
        attempts: int = 1,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        output_text: str | None = None,
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
            "system_prompt_sha256": _hash_text(system_prompt),
            "user_prompt_sha256": _hash_text(user_prompt),
            "output_sha256": _hash_text(output_text),
        }

    def _chat_completion(self, payload: dict[str, Any], timeout: int) -> tuple[dict[str, Any], int]:
        attempts = 0
        last_error: requests.RequestException | None = None
        max_attempts = max(1, self.max_retries + 1)
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
        max_attempts = max(1, self.max_retries + 1)
        payload = {
            "model": self.model_name(),
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
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
                    timeout=self.timeout_seconds,
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
                    "model": self.model_name(),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
                timeout=self.timeout_seconds,
            )
        content = self._content_from_response(data)
        return LLMResult(
            content=content,
            metadata=self._metadata(
                started_at,
                data,
                attempts,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output_text=content,
            ),
        )

    def advisory_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        result = self.advisory_completion_result(system_prompt, user_prompt)
        return result.content if result else None

    def structured_json_result(self, system_prompt: str, user_prompt: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not self.enabled():
            return None
        started_at = time.perf_counter()
        request_user_prompt = user_prompt
        if self.provider_name == "anthropic":
            json_instruction = "\n\nReturn only a valid JSON object. Do not include markdown fences."
            request_user_prompt = user_prompt + json_instruction
            data, attempts = self._anthropic_completion(system_prompt, request_user_prompt)
        else:
            payload: dict[str, Any] = {
                "model": self.model_name(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            if self.provider_name == "openai_compatible":
                json_instruction = "\n\nReturn only a valid JSON object. Do not include markdown fences."
                request_user_prompt = user_prompt + json_instruction
                payload["messages"][1]["content"] = request_user_prompt
            else:
                payload["response_format"] = {"type": "json_object"}
            data, attempts = self._chat_completion(
                payload,
                timeout=self.timeout_seconds,
            )
        content = self._content_from_response(data)
        parsed = json.loads(content)
        return parsed, self._metadata(
            started_at,
            data,
            attempts,
            system_prompt=system_prompt,
            user_prompt=request_user_prompt,
            output_text=content,
        )

    def structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        result = self.structured_json_result(system_prompt, user_prompt)
        return result[0] if result else None


def _hash_text(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
