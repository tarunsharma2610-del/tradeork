from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret, encrypt_secret
from app.repositories.broker_connections import BrokerConnectionRepository
from app.schemas.broker_connection import (
    BrokerConnectionCreate,
    BrokerConnectionRead,
    BrokerConnectionUpdate,
    mask_secret,
)
from app.services.upstox_broker import UpstoxBrokerAdapter

_MAX_CONNECTIONS_PER_USER = 5


class BrokerConnectionService:
    """Per-user broker credential store (Settings → "Add Upstox API").

    Secrets are encrypted at rest via :func:`encrypt_secret` and only ever
    returned as masked previews. Live execution resolves the current user's
    stored credentials through :func:`get_broker_for_user` so every user can
    trade through their own broker account.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BrokerConnectionRepository(db)

    # ------------------------------------------------------------------ #
    # Read models
    # ------------------------------------------------------------------ #
    def _to_read(self, connection) -> BrokerConnectionRead:
        access_token = decrypt_secret(connection.access_token_encrypted)
        api_key = (
            decrypt_secret(connection.api_key_encrypted)
            if connection.api_key_encrypted
            else None
        )
        return BrokerConnectionRead(
            id=connection.id,
            user_id=connection.user_id,
            provider=connection.provider,
            label=connection.label,
            access_token_masked=mask_secret(access_token),
            api_key_masked=mask_secret(api_key) if api_key else None,
            is_active=connection.is_active,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def list(self, user_id: UUID) -> list[BrokerConnectionRead]:
        connections = self.repo.list_for_user(user_id)
        return [self._to_read(c) for c in connections]

    def get(self, user_id: UUID, connection_id: UUID) -> BrokerConnectionRead:
        connection = self.repo.get_for_user(user_id, connection_id)
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found.",
            )
        return self._to_read(connection)

    def create(
        self, user_id: UUID, data: BrokerConnectionCreate
    ) -> BrokerConnectionRead:
        existing = self.repo.list_for_user(user_id)
        if len(existing) >= _MAX_CONNECTIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"You can have at most {_MAX_CONNECTIONS_PER_USER} broker "
                    "connections."
                ),
            )
        connection = self.repo.create(
            user_id=user_id,
            provider=data.provider.value,
            label=data.label,
            access_token_encrypted=encrypt_secret(data.access_token),
            api_key_encrypted=(
                encrypt_secret(data.api_key) if data.api_key else None
            ),
        )
        self.db.commit()
        self.db.refresh(connection)
        return self._to_read(connection)

    def update(
        self,
        user_id: UUID,
        connection_id: UUID,
        data: BrokerConnectionUpdate,
    ) -> BrokerConnectionRead:
        connection = self.repo.get_for_user(user_id, connection_id)
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found.",
            )
        if data.label is not None:
            connection.label = data.label
        if data.access_token is not None:
            connection.access_token_encrypted = encrypt_secret(data.access_token)
        if data.api_key is not None:
            connection.api_key_encrypted = encrypt_secret(data.api_key)
        if data.is_active is not None:
            connection.is_active = data.is_active
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return self._to_read(connection)

    def delete(self, user_id: UUID, connection_id: UUID) -> None:
        connection = self.repo.get_for_user(user_id, connection_id)
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Broker connection not found.",
            )
        self.db.delete(connection)
        self.db.commit()

    # ------------------------------------------------------------------ #
    # Execution resolution
    # ------------------------------------------------------------------ #
    def resolve_adapter(self, user_id: UUID) -> UpstoxBrokerAdapter | None:
        """Build a live Upstox adapter from the user's stored credentials.

        Returns ``None`` when the user has no active connection — callers then
        fall back to the server-configured adapter.
        """
        connection = self.repo.get_active_for_user(user_id, "upstox")
        if connection is None:
            return None
        access_token = decrypt_secret(connection.access_token_encrypted)
        api_key = (
            decrypt_secret(connection.api_key_encrypted)
            if connection.api_key_encrypted
            else ""
        )
        return UpstoxBrokerAdapter(
            api_key=api_key,
            access_token=access_token,
        )
