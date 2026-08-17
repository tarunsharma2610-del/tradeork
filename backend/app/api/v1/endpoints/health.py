from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis_client

router = APIRouter(tags=["health"])


@router.get("/health", response_model=dict)
async def health(db: Session = Depends(get_db)) -> dict:
    db_status = "ok"
    redis_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"
    try:
        client = get_redis_client()
        await client.ping()
    except Exception:
        redis_status = "unavailable"
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "ok" if (db_status == "ok" and redis_status == "ok") else "degraded",
            "database": db_status,
            "redis": redis_status,
            "environment": settings.ENVIRONMENT,
        },
    )
