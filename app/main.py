from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.db.session import check_migrations, engine

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_starting", environment=settings.environment)
    await check_migrations()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
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
