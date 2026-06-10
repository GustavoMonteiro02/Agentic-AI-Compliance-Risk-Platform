from pathlib import Path

from app.config import get_settings
from app.rag.ingest import ingest_qdrant


def main() -> None:
    settings = get_settings()
    summary = ingest_qdrant(Path(settings.knowledge_base_path))
    print(summary)


if __name__ == "__main__":
    main()
