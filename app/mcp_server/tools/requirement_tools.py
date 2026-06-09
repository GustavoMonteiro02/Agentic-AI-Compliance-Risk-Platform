from app.rag.retriever import LocalComplianceRetriever


def search_regulatory_requirements(query: str, top_k: int = 6) -> list[dict]:
    return LocalComplianceRetriever().search(query, top_k=top_k)

