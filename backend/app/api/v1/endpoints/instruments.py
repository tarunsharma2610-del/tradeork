from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import rate_limit_dependency
from app.domain.enums import Exchange, InstrumentType
from app.schemas.instrument import InstrumentRead
from app.services.instruments import InstrumentService

router = APIRouter(prefix="/instruments", tags=["instruments"])

search_rate_limit = rate_limit_dependency("instruments:search", 60, 60)


@router.get(
    "",
    response_model=list[InstrumentRead],
    dependencies=[Depends(search_rate_limit)],
)
async def search_instruments(
    q: str | None = Query(default=None, max_length=100),
    exchange: Exchange | None = None,
    instrument_type: InstrumentType | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list:
    return InstrumentService(db).search(
        query=q,
        exchange=exchange.value if exchange else None,
        instrument_type=instrument_type.value if instrument_type else None,
        limit=limit,
    )


@router.get("/{instrument_id}", response_model=InstrumentRead)
async def get_instrument(
    instrument_id: UUID,
    db: Session = Depends(get_db),
):
    return InstrumentService(db).get(instrument_id)
