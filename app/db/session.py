import asyncio
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = structlog.get_logger(__name__)
engine = create_async_engine(
    settings.database_url,
    pool_recycle=settings.db_pool_recycle_seconds,
    pool_pre_ping=True,
    connect_args={
        "timeout": settings.db_connect_timeout_seconds,
        "command_timeout": settings.db_statement_timeout_ms / 1000,
    },
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

alembic_config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
project_root = Path(__file__).resolve().parents[2]


def _database_revision_heads(connection) -> tuple[list[str], list[str]]:
    """The DB's current Alembic head revisions, and the heads defined by scripts on disk."""
    migration_context = MigrationContext.configure(connection=connection)
    current_heads = migration_context.get_current_heads()
    script_heads = ScriptDirectory.from_config(alembic_config).get_heads()
    return current_heads, script_heads


def _run_alembic_upgrade() -> None:
    """Shell out to `alembic upgrade head` synchronously (run off the event loop by the caller)."""
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )


async def _maybe_upgrade_database() -> bool:
    """Run `alembic upgrade head` if the DB's heads differ from scripts'; return whether it ran."""
    async with engine.begin() as conn:
        current_heads, script_heads = await conn.run_sync(_database_revision_heads)

    if set(current_heads) == set(script_heads):
        return False

    await asyncio.to_thread(_run_alembic_upgrade)
    return True


async def check_migrations() -> None:
    """Self-upgrade the DB to the latest Alembic head at startup, if it isn't already there."""
    updated = await _maybe_upgrade_database()
    if updated:
        logger.info("Database migrations were applied successfully.")
    else:
        logger.info("Database migrations are already up-to-date.")


async def get_db() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency: yield a request-scoped AsyncSession, closed after the request."""
    async with AsyncSessionLocal() as session:
        yield session
