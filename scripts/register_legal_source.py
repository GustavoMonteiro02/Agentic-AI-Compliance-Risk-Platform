import argparse

from app.config import get_settings
from app.rag.legal_sources import register_legal_source


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register a local official legal source in the RAG manifest.")
    parser.add_argument("--id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--jurisdiction", required=True)
    parser.add_argument("--authority", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--document-type", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--expected-article-count", type=int, default=None)
    parser.add_argument("--required-locator", action="append", default=[])
    parser.add_argument("--ingestion-status", default="available")
    parser.add_argument("--notes", default="Registered local official-source document.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    source = {
        "id": args.id,
        "title": args.title,
        "jurisdiction": args.jurisdiction,
        "authority": args.authority,
        "source_url": args.source_url,
        "document_type": args.document_type,
        "local_path": args.local_path,
        "expected_article_count": args.expected_article_count,
        "minimum_required_locators": args.required_locator,
        "ingestion_status": args.ingestion_status,
        "notes": args.notes,
    }
    print(register_legal_source(get_settings().knowledge_base_path, source))
