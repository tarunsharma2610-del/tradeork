from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.repositories.base import BaseRepository


class BrokerConnectionRepository(BaseRepository[BrokerConnection]):
    model = BrokerConnection

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def list_for_user(self, user_id: UUID) -> list[BrokerConnection]:
        stmt = (
            select(BrokerConnection)
            .where(BrokerConnection.user_id == user_id)
            .order_by(BrokerConnection.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_for_user(
        self, user_id: UUID, connection_id: UUID
    ) -> BrokerConnection | None:
        stmt = select(BrokerConnection).where(
            BrokerConnection.id == connection_id,
            BrokerConnection.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def get_active_for_user(
        self, user_id: UUID, provider: str
    ) -> BrokerConnection | None:
        stmt = (
            select(BrokerConnection)
            .where(
                BrokerConnection.user_id == user_id,
                BrokerConnection.provider == provider,
                BrokerConnection.is_active.is_(True),
            )
            .order_by(BrokerConnection.updated_at.desc())
        )
        return self.db.scalars(stmt).first()

    def create(
        self,
        *,
        user_id: UUID,
        provider: str,
        label: str | None,
        access_token_encrypted: str,
        api_key_encrypted: str | None,
    ) -> BrokerConnection:
        connection = BrokerConnection(
            user_id=user_id,
            provider=provider,
            label=label,
            access_token_encrypted=access_token_encrypted,
            api_key_encrypted=api_key_encrypted,
        )
        self.db.add(connection)
        return connection
