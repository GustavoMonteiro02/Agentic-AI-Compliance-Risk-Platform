import json
from typing import Any

import requests

from app.config import get_settings


class OptionalLLMProvider:
    """Small optional OpenAI adapter.

    The deterministic workflow remains the default. This adapter only runs when
    `AI_GENERATION_MODE=openai` and `OPENAI_API_KEY` are configured.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def enabled(self) -> bool:
        return self.settings.ai_generation_mode == "openai" and bool(self.settings.openai_api_key)

    def advisory_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        if not self.enabled():
            return None
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
        return data["choices"][0]["message"]["content"]

    def structured_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
        if not self.enabled():
            return None
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
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
