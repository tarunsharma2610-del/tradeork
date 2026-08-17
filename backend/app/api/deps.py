import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_jwt_token
from app.models.user import User
from app.repositories.users import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_jwt_token(token)
    except jwt.InvalidTokenError:
        raise _credentials_exc from None
    if payload.get("type") != "access":
        raise _credentials_exc
    sub = payload.get("sub")
    try:
        user_id = uuid.UUID(sub) if sub else None
    except (TypeError, ValueError):
        user_id = None
    if user_id is None:
        raise _credentials_exc
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise _credentials_exc
    return user
