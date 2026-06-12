from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.rag.ingest import ingest_pinecone


if __name__ == "__main__":
    print(ingest_pinecone(get_settings().knowledge_base_path))
