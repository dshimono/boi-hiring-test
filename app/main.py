from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.router import api_router
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.db.session import check_migrations, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_migrations()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(lifespan=lifespan)
    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
