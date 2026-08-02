from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic_settings import BaseSettings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
    )


settings = Settings()
engine = create_async_engine(settings.database_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "Hello from fastapi-datallmreact!"}


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        version = await conn.scalar(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
    return {"status": "ok", "pgvector_version": version}
