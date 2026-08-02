from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "Hello from fastapi-datallmreact!"}


@router.get("/health/live")
def health_live():
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    version = await db.scalar(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
    return {"status": "ok", "pgvector_version": version}
