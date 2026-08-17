from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, instruments, market, portfolios, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(portfolios.router)
api_router.include_router(instruments.router)
api_router.include_router(market.router)
