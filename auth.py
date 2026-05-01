from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.init_db import get_db
from db.model_notes import User
from utils.hash_password import verify_password

security = HTTPBasic()


async def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """
    HTTP Basic authentication.

    [HTTP Basic Auth] The browser itself typically caches the credentials
    for the duration of the session and automatically re-sends them in the
    Authorization header on subsequent requests — so the login prompt usually
    only appears once per browser session, not on every request. However, this is
    browser behavior, not something HTTPBasic or FastAPI controls directly.
    """

    result = await session.execute(select(User).where(User.name == credentials.username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
