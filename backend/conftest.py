"""Pytest fixtures: in-memory DB, mocked auth, and a FastAPI test client."""

import asyncio
import os
import uuid

# Provide required config values before the app modules are imported, so the
# cached `settings` object can be built without a real Supabase/Postgres/OpenAI.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import String
from sqlalchemy.dialects.sqlite import base as sqlite_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

import app.database.base as db_base
import app.chat.persistence as chat_persistence
import app.chat.routes as chat_routes
from app.auth.dependencies import CurrentUser, get_current_user
from app.database.base import Base, get_session
from app.database.models.user import User


# SQLite can't render the Postgres-native JSONB type. For the in-memory test
# database only, map JSONB to SQLite's JSON affinity so create_all succeeds.
sqlite_base.SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "JSON"


class _UUIDAsString(TypeDecorator):
    """Store UUIDs as 36-char strings on SQLite to avoid numeric coercion.

    Production uses Postgres native UUID; this only affects the test engine.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return uuid.UUID(value) if value is not None else None


TEST_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
TEST_USER_EMAIL = "test@example.com"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(
        "sqlite+aiosqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session", autouse=True)
def _prepare_db(engine):
    # Import the app so all models register on Base.metadata. The chat tests
    # only need these three tables; create just those (the full metadata
    # includes Postgres-only types such as pgvector VECTOR and JSONB defaults
    # that SQLite cannot render).
    from app.main import app  # noqa: F401

    chat_tables = [
        Base.metadata.tables["users"],
        Base.metadata.tables["chat_threads"],
        Base.metadata.tables["chat_messages"],
    ]

    # Swap native Postgres UUID columns for string-backed UUIDs so SQLite does
    # not coerce 32-hex-digit ids into floats. Test-scoped only.
    for table in chat_tables:
        for column in table.columns:
            if column.type.__class__.__name__ == "UUID":
                column.type = _UUIDAsString()

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=chat_tables)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with factory() as seed:
            seed.add(User(id=TEST_USER_ID, email=TEST_USER_EMAIL))
            await seed.commit()

    asyncio.run(_setup())
    yield


@pytest.fixture
def client(engine, monkeypatch):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _single_session():
        async with factory() as s:
            yield s

    # Background-task persistence opens its own session via SessionLocal.
    monkeypatch.setattr(db_base, "SessionLocal", factory)
    monkeypatch.setattr(chat_persistence, "SessionLocal", factory)
    monkeypatch.setattr(chat_routes, "SessionLocal", factory)

    from app.main import app

    app.dependency_overrides[get_session] = _single_session
    app.dependency_overrides[get_current_user] = _override_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _override_current_user() -> CurrentUser:
    return CurrentUser(id=TEST_USER_ID, email=TEST_USER_EMAIL)
