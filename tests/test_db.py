import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.mark.asyncio
async def test_postgres_container(async_engine):
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))

    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_migration(async_engine):
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
        )

        tables = result.scalars().all()
        print(f"---------------------------------------------{tables}")

    assert "users" in tables
    assert "notes" in tables
    assert "files" in tables