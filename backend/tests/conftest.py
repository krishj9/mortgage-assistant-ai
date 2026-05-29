from __future__ import annotations

import os
import sys
import uuid

import pytest
import pytest_asyncio
import psycopg
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


# Postgres-only test harness.
# Creates an ephemeral test database per pytest session.
POSTGRES_ADMIN_URL = os.environ.get(
    "POSTGRES_ADMIN_URL",
    "postgresql://loanofficer:loanofficer_password@localhost:5432/postgres",
)

_test_db_name = f"loanofficer_test_{uuid.uuid4().hex[:10]}"
_test_db_url = f"postgresql+psycopg://loanofficer:loanofficer_password@localhost:5432/{_test_db_name}"

# Always isolate tests from a developer's local DATABASE_URL (e.g. loanofficer_mvp).
os.environ["DATABASE_URL"] = _test_db_url
os.environ.setdefault("JWT_SECRET", "test-secret")

# Ensure local imports like `import app` work under pytest import modes.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    # Create ephemeral test database
    with psycopg.connect(POSTGRES_ADMIN_URL, autocommit=True) as conn:
        conn.execute(f'CREATE DATABASE "{_test_db_name}"')

    Base.metadata.create_all(bind=engine)
    yield

    # Best-effort cleanup: drop test database after session.
    try:
        with psycopg.connect(POSTGRES_ADMIN_URL, autocommit=True) as conn:
            # terminate connections first
            conn.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s",
                (_test_db_name,),
            )
            conn.execute(f'DROP DATABASE IF EXISTS "{_test_db_name}"')
    except Exception:
        # Cleanup failures should not fail the test run.
        pass


@pytest.fixture
def app() -> FastAPI:
    return fastapi_app


@pytest_asyncio.fixture
async def async_client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

