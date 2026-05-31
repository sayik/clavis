import pytest_asyncio

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from main import app
from db.init_db import get_db
from auth import get_current_user
from db.model_notes import Base, User, File, Note

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSession = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest_asyncio.fixture(autouse=True)
async def setup_database():

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



async def override_get_db():
    async with TestingSession() as session:
        yield session


def override_get_current_user():
    return User(
        id=1,
        name="test",
        email="test@example.com",
        password_hash="newpassword",
    )


@pytest_asyncio.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
