import secrets
from redis_fastapi import AsyncRedisDep
from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from config.settings import WS_TOKEN_TTL
from ..db.init_db import get_db
from app.auth.user_handler import get_user_by_id
from exception import UnauthorizedException
from app.db.models import User


def generate_token():
    token = secrets.token_urlsafe(16)
    return token


async def validate_user_id(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await get_user_by_id(
        user_id=user_id,
        session=session,
    )

    if user is None:
        raise UnauthorizedException(
            detail="Unauthorized"
        )

    return user


async def create_token(redis: AsyncRedisDep, user_id: str) -> str:
    """Here create_token creates token and saves
    key value pair in redis cache.
    redis: AsyncRedisDep - redis connector
    user_id: str - logged in user_id"""
    token = generate_token()
    redis.set(token, user_id, ex=WS_TOKEN_TTL)
    return token ## send this token to the router function that calls for Token


async def consume_token(redis: AsyncRedisDep, user_id: str):
    pass

# async def validate_user_id(user_id: str) -> bool:
#     session = get_db()
#     user = await get_user_by_id(
#         user_id=user_id,
#         session=session,
#     )

#     if user is None:
#         raise UnauthorizedException(detail="Unauthorized")

#     return user
