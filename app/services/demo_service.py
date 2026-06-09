import json
from pathlib import Path

from app.config import get_settings


class DemoScenarioService:
    def __init__(self) -> None:
        self.sample_path = get_settings().knowledge_base_path / "sample_ai_systems"

    def list(self) -> list[dict]:
        scenarios = []
        for path in sorted(self.sample_path.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            scenarios.append({"slug": path.stem, **payload})
        return scenarios

    def get(self, slug: str) -> dict:
        path = self.sample_path / f"{slug}.json"
        if not path.exists():
            raise FileNotFoundError(slug)
        return json.loads(path.read_text(encoding="utf-8"))
