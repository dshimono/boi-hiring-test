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
    from scripts.seed_from_source import seed

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(func.count()).select_from(Ad))
    if existing:
        return
    logger.info("database_empty_seeding")
    await seed(force=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_starting", environment=settings.environment)
    await check_migrations()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await seed_if_empty()
    logger.info("application_started")
    yield
    logger.info("application_stopping")
    await engine.dispose()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(lifespan=lifespan)
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router)
    Path(settings.static_dir).mkdir(parents=True, exist_ok=True)
    app.mount("/static/ads", StaticFiles(directory=settings.static_dir), name="ads-static")
    return app


app = create_app()
