from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.services.email import EmailService

# Shared across integration and e2e, which both run against a real Postgres
# instance and a real app. Unit tests override `db_session` with an in-memory
# SQLite fixture (see tests/unit/conftest.py) — pytest resolves fixtures from
# the conftest closest to the test, so that override wins there automatically.


@pytest.fixture(autouse=True)
def _stub_email_service(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub EmailService so tests don't hit the real Resend API.

    Tests marked @pytest.mark.real_email (e.g. test_email.py) opt out of this
    and exercise the real implementation instead.
    """
    if request.node.get_closest_marker("real_email"):
        return
    monkeypatch.setattr(EmailService, "send_magic_link", AsyncMock(return_value=None))


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """A session against settings.database_url (same DB as docker compose), rolled back after."""
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    connection = await engine.connect()
    transaction = await connection.begin()

    # Bind the session to the already-open transaction via a savepoint, so the
    # test's own commit()/rollback() calls don't escape the outer transaction —
    # everything is undone in one rollback() below, keeping tests isolated and repeatable.
    session_factory = async_sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )

    async with session_factory() as session:
        yield session

    await transaction.rollback()
    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """An HTTP client wired to the app with get_db overridden to db_session."""
    app = create_app()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
