from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import models
from app.rag.retriever import LocalComplianceRetriever


def seed_requirements(db: Session) -> int:
    """Seed requirement rows from the local Markdown knowledge base."""
    chunks = LocalComplianceRetriever().load()
    created = 0
    for chunk in chunks:
        existing = db.scalar(
            select(models.Requirement).where(models.Requirement.requirement_code == chunk.requirement_id)
        )
        if existing:
            existing.title = chunk.title
            existing.description = chunk.text
            existing.source = chunk.source
            existing.category = chunk.category
            continue
        db.add(
            models.Requirement(
                requirement_code=chunk.requirement_id,
                title=chunk.title,
                description=chunk.text,
                source=chunk.source,
                category=chunk.category,
            )
        )
        created += 1
    db.commit()
    return created
