from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit_dependency
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.audit import record_audit
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

login_rate_limit = rate_limit_dependency("auth:login", 10, 60)
register_rate_limit = rate_limit_dependency("auth:register", 5, 60)


def _request_context(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip, user_agent


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path="/",
    )


def _build_response(response: Response, access: str, refresh: str, expires_in: int):
    _set_refresh_cookie(response, refresh)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
    )


def _resolve_refresh_token(data: RefreshRequest | LogoutRequest, request: Request) -> str:
    token = data.refresh_token or request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing.",
        )
    return token


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_rate_limit)],
)
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    ip, user_agent = _request_context(request)
    user, access, refresh, expires_in = AuthService(db).register(
        data, ip_address=ip, user_agent=user_agent
    )
    record_audit(
        db,
        user_id=user.id,
        action="auth.register",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip,
        user_agent=user_agent,
    )
    return _build_response(response, access, refresh, expires_in)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(login_rate_limit)],
)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    ip, user_agent = _request_context(request)
    user, access, refresh, expires_in = AuthService(db).authenticate(
        data, ip_address=ip, user_agent=user_agent
    )
    record_audit(
        db,
        user_id=user.id,
        action="auth.login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip,
        user_agent=user_agent,
    )
    return _build_response(response, access, refresh, expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    raw_refresh = _resolve_refresh_token(data, request)
    ip, user_agent = _request_context(request)
    user, access, new_refresh, expires_in = AuthService(db).refresh(
        raw_refresh, ip_address=ip, user_agent=user_agent
    )
    record_audit(
        db,
        user_id=user.id,
        action="auth.refresh",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip,
        user_agent=user_agent,
    )
    return _build_response(response, access, new_refresh, expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: LogoutRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> Response:
    raw_refresh = _resolve_refresh_token(data, request)
    AuthService(db).logout(raw_refresh)
    response.delete_cookie("refresh_token", path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
