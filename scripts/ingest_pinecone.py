from app.config import get_settings
from app.rag.ingest import ingest_pinecone


if __name__ == "__main__":
    print(ingest_pinecone(get_settings().knowledge_base_path))
