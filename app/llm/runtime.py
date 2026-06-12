from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRuntimeConfig:
    ai_generation_mode: str | None = None
    llm_provider: str | None = None
    model: str | None = None
    timeout_seconds: int | None = None
    max_retries: int | None = None
    max_tokens: int | None = None
    temperature: float | None = None


_runtime_config: ContextVar[LLMRuntimeConfig | None] = ContextVar("llm_runtime_config", default=None)


def get_llm_runtime_config() -> LLMRuntimeConfig | None:
    return _runtime_config.get()


def set_llm_runtime_config(config: LLMRuntimeConfig | None):
    return _runtime_config.set(config)


def reset_llm_runtime_config(token) -> None:
    _runtime_config.reset(token)
