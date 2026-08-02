from fastapi import APIRouter

from app.api.routes import ads, health, metrics, stats

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ads.router, prefix="/api/v1")
api_router.include_router(metrics.router, prefix="/api/v1")
api_router.include_router(stats.router, prefix="/api/v1")
