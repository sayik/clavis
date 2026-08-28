import pytest_asyncio
import pytest

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from faker import Faker

from testcontainers.core.docker_client import DockerClient

from testcontainers.postgres import PostgresContainer

from app.main import app
from app.db.init_db import get_db
from app.auth import get_current_user
from app.db.models import Base, User, File, Note


def is_docker_running() -> bool:
    try:
        DockerClient()
        return True
    except Exception:
        return False



@pytest_asyncio.fixture(scope="session")
async def pg_container():
    """Create a PostgreSQL container for testing."""
    if not is_docker_running():
        pytest.skip("Docker is required, but not running")

    with PostgresContainer() as pg:
        yield pg


@pytest_asyncio.fixture(scope="session")
async def test_db_url(pg_container):
    return pg_container.get_connection_url().replace(
        "postgresql://",
        "postgresql+asyncpg://",
    )

@pytest_asyncio.fixture(scope="session")
async def alembic_migrations(test_db_url):
    config = Config("alembic.ini")

    config.set_main_option("sqlalchemy.url", test_db_url,)

    command.upgrade(config, "head")


@pytest_asyncio.fixture(scope="session")
async def async_engine(alembic_migrations, test_db_url):
    engine = create_async_engine(test_db_url)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def override_get_db(async_engine):
    TestingSession = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
    )

    async def _override_get_db():
        async with TestingSession() as session:
            yield session

    return _override_get_db



def override_get_current_user():
    return User(
        id=1,
        name="test",
        email="test@example.com",
        password_hash="newpassword",
    )


@pytest.fixture()
def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
