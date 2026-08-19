from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.broker_connection import (
    BrokerConnectionCreate,
    BrokerConnectionRead,
    BrokerConnectionUpdate,
)
from app.services.broker_connections import BrokerConnectionService

router = APIRouter(prefix="/settings/broker", tags=["settings"])


@router.get("", response_model=list[BrokerConnectionRead])
async def list_broker_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BrokerConnectionRead]:
    return BrokerConnectionService(db).list(current_user.id)


@router.post(
    "",
    response_model=BrokerConnectionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_broker_connection(
    data: BrokerConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrokerConnectionRead:
    return BrokerConnectionService(db).create(current_user.id, data)


@router.patch(
    "/{connection_id}",
    response_model=BrokerConnectionRead,
)
async def update_broker_connection(
    connection_id: UUID,
    data: BrokerConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BrokerConnectionRead:
    return BrokerConnectionService(db).update(
        current_user.id, connection_id, data
    )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_broker_connection(
    connection_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    BrokerConnectionService(db).delete(current_user.id, connection_id)
