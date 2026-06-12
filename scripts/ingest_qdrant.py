from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.rag.ingest import ingest_qdrant


def main() -> None:
    settings = get_settings()
    summary = ingest_qdrant(Path(settings.knowledge_base_path))
    print(summary)


if __name__ == "__main__":
    main()
