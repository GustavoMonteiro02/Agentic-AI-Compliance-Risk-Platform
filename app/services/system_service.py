from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.repositories import SystemRepository
from app.schemas.system import AISystemCreate, AISystemUpdate


class SystemService:
    def __init__(self, db: Session) -> None:
        self.repo = SystemRepository(db)

    def create(self, payload: AISystemCreate):
        return self.repo.create(payload)

    def list(self):
        return self.repo.list()

    def get(self, system_id: str):
        system = self.repo.get(system_id)
        if not system:
            raise HTTPException(status_code=404, detail="AI system not found")
        return system

    def update(self, system_id: str, payload: AISystemUpdate):
        return self.repo.update(self.get(system_id), payload)

