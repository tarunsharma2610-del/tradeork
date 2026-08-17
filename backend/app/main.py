import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis import close_redis
from app.services.auth import AuthError
from app.services.paper_engine import run_paper_matcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    matcher_task = None
    if settings.PAPER_MATCHER_ENABLED and settings.ENVIRONMENT != "test":
        matcher_task = asyncio.create_task(run_paper_matcher())
    try:
        yield
    finally:
        if matcher_task is not None:
            matcher_task.cancel()
            try:
                await matcher_task
            except Exception:
                pass
        await close_redis()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AuthError)
async def auth_error_handler(request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.message}
    )


@app.get("/")
async def root() -> dict:
    return {"service": settings.PROJECT_NAME, "status": "ok"}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
