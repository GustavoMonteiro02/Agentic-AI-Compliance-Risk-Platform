from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import models


class RequirementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[models.Requirement]:
        return list(self.db.scalars(select(models.Requirement).order_by(models.Requirement.source)))

    def search(self, query: str) -> list[models.Requirement]:
        pattern = f"%{query}%"
        return list(
            self.db.scalars(
                select(models.Requirement)
                .where(
                    or_(
                        models.Requirement.requirement_code.ilike(pattern),
                        models.Requirement.title.ilike(pattern),
                        models.Requirement.description.ilike(pattern),
                        models.Requirement.category.ilike(pattern),
                        models.Requirement.source.ilike(pattern),
                    )
                )
                .order_by(models.Requirement.source)
            )
        )
