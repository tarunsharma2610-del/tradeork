import secrets

from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_jwt_token,
    ensure_aware,
    hash_password,
    hash_token,
    utcnow,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_tokens import RefreshTokenRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthError(Exception):
    """Business-level authentication error surfaced as an HTTP error."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def register(
        self,
        data: RegisterRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[User, str, str, int]:
        email = data.email.lower()
        if self.users.get_by_email(email) is not None:
            raise AuthError(
                "An account with this email already exists.",
                status_code=status.HTTP_409_CONFLICT,
            )
        user = self.users.create(
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
        )
        access, refresh, expires_in = self._issue_tokens(
            user, ip_address=ip_address, user_agent=user_agent
        )
        return user, access, refresh, expires_in

    def authenticate(
        self,
        data: LoginRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[User, str, str, int]:
        user = self.users.get_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.password_hash):
            raise AuthError("Incorrect email or password.")
        if not user.is_active:
            raise AuthError("This account is disabled.", status_code=status.HTTP_403_FORBIDDEN)
        user.last_login_at = utcnow()
        self.db.add(user)
        access, refresh, expires_in = self._issue_tokens(
            user, ip_address=ip_address, user_agent=user_agent
        )
        return user, access, refresh, expires_in

    def refresh(
        self,
        raw_refresh: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[User, str, str, int]:
        record = self.refresh_tokens.get_by_token_hash(hash_token(raw_refresh))
        if record is None or record.revoked_at is not None:
            raise AuthError("Invalid refresh token.")
        if ensure_aware(record.expires_at) < utcnow():
            raise AuthError("Refresh token has expired.")
        user = self.users.get(record.user_id)
        if user is None or not user.is_active:
            raise AuthError(
                "User no longer exists or is disabled.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        access, new_refresh, expires_in = self._issue_tokens(
            user, ip_address=ip_address, user_agent=user_agent
        )
        record.revoked_at = utcnow()
        self.db.add(record)
        self.db.commit()
        return user, access, new_refresh, expires_in

    def logout(self, raw_refresh: str) -> None:
        record = self.refresh_tokens.get_by_token_hash(hash_token(raw_refresh))
        if record is not None and record.revoked_at is None:
            record.revoked_at = utcnow()
            self.db.add(record)
            self.db.commit()

    def _issue_tokens(
        self,
        user: User,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> tuple[str, str, int]:
        access = create_jwt_token(
            str(user.id), "access", settings.access_token_expires
        )
        raw_refresh = secrets.token_urlsafe(48)
        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(raw_refresh),
                expires_at=utcnow() + settings.refresh_token_expires,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )
        self.db.commit()
        return access, raw_refresh, int(settings.access_token_expires.total_seconds())
