from app.config import get_settings
from app.rag.ingest import legal_source_summary


if __name__ == "__main__":
    summary = legal_source_summary(get_settings().knowledge_base_path)
    print(summary)
    raise SystemExit(0 if summary.get("validation", {}).get("ready") else 1)
