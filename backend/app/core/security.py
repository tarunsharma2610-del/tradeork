import base64
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from cryptography.fernet import Fernet

from app.core.config import settings

_ph = PasswordHasher()


def _get_fernet() -> Fernet:
    """Build a Fernet cipher keyed deterministically off SECRET_KEY.

    The same SECRET_KEY always yields the same cipher, so stored secrets stay
    decryptable across restarts. Rotating SECRET_KEY invalidates stored
    secrets — acceptable for this deployment; documented in .env.example.
    """
    key = base64.urlsafe_b64encode(sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret (e.g. a broker access token) at rest."""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a secret previously stored with :func:`encrypt_secret`."""
    return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_jwt_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def utcnow() -> datetime:
    return datetime.now(UTC)


def ensure_aware(dt: datetime) -> datetime:
    """Attach UTC tzinfo to naive datetimes.

    SQLite returns naive datetimes even for timezone-aware columns while
    PostgreSQL returns aware ones. Normalising keeps comparisons consistent
    across backends.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
