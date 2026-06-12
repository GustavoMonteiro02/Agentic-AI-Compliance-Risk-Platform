from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


EDITABLE_RUNTIME_KEYS = {
    "ai_generation_mode",
    "llm_provider",
    "openai_api_key",
    "openai_base_url",
    "openai_model",
    "openai_timeout_seconds",
    "openai_max_retries",
    "openai_max_tokens",
    "anthropic_api_key",
    "anthropic_base_url",
    "anthropic_model",
    "langsmith_tracing",
    "langsmith_api_key",
    "langsmith_project",
    "vector_db",
    "qdrant_url",
    "qdrant_collection",
    "embedding_provider",
    "openai_embedding_model",
    "embedding_dimensions",
}

SENSITIVE_RUNTIME_KEYS = {
    "openai_api_key",
    "anthropic_api_key",
    "langsmith_api_key",
}


def runtime_config_path() -> Path:
    return Path(os.getenv("RUNTIME_CONFIG_PATH", ".runtime-config.json"))


def load_runtime_overrides() -> dict[str, Any]:
    path = runtime_config_path()
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        return {}
    return {key: value for key, value in data.items() if key in EDITABLE_RUNTIME_KEYS}


def save_runtime_overrides(updates: dict[str, Any]) -> dict[str, Any]:
    current = load_runtime_overrides()
    for key, value in updates.items():
        if key not in EDITABLE_RUNTIME_KEYS:
            continue
        current[key] = value

    path = runtime_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return current


def has_runtime_override(key: str) -> bool:
    return key in load_runtime_overrides()
