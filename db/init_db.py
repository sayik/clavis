from typing import Annotated, AsyncIterator

from fastapi import Depends
# from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from db.model_notes import Base, User, Note, File

DB_URI = "sqlite+aiosqlite:///./notes.db"

async_engine = create_async_engine(
    DB_URI,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise

SessionDep = Annotated[AsyncSession, Depends(get_db)]

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())