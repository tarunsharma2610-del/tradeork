from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.repositories.instruments import InstrumentRepository


class InstrumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InstrumentRepository(db)

    def search(
        self,
        *,
        query: str | None = None,
        exchange: str | None = None,
        instrument_type: str | None = None,
        limit: int = 50,
    ) -> list[Instrument]:
        limit = max(1, min(limit, 100))
        return self.repo.search(
            query=query,
            exchange=exchange,
            instrument_type=instrument_type,
            limit=limit,
        )

    def get(self, instrument_id: UUID) -> Instrument:
        instrument = self.repo.get(instrument_id)
        if instrument is None or not instrument.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instrument not found.",
            )
        return instrument
