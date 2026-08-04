from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.db.session import AsyncSessionLocal, check_migrations, engine
from app.models import Ad

logger = structlog.get_logger(__name__)


async def seed_if_empty() -> None:
    """Load source/*.csv into the ads tables on first boot, if the ads table is empty."""
    from scripts.seed_from_source import seed

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Ad))
    if existing:
        return
    logger.info("Ads table is empty; seeding from source data.")
    await seed(force=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: migrate, provision pgvector, seed if empty. Shutdown: dispose the engine."""
    # uvicorn re-applies its own default logging config (re-adding uvicorn.access's
    # handler) after create_app() has already run, so re-silence it here to avoid
    # duplicate request logs (ours from middleware + uvicorn's own access line).
    configure_logging()
    logger.info("Starting application.", environment=settings.environment)
    await check_migrations()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await seed_if_empty()
    logger.info("Application startup complete.")
    yield
    logger.info("Shutting down application.")
    await engine.dispose()


def create_app() -> FastAPI:
    """Build the FastAPI app: logging, middleware, exception handlers, routes, static ad images."""
    configure_logging()
    app = FastAPI(lifespan=lifespan)
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router)
    Path(settings.static_dir).mkdir(parents=True, exist_ok=True)
    app.mount("/static/ads", StaticFiles(directory=settings.static_dir), name="ads-static")
    return app


app = create_app()
