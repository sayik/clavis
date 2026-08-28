# file name connector? link? Bridge?
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.user_handler import get_user_by_id
from app.exception import UnauthorizedException
from ..db.init_db import get_db
from app.auth.password_handler import verify_password, get_password_hash
from .token_handler import decode_access_token
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db)], token: Annotated[str, Depends(oauth2_scheme)]
):
    try:
        payload = decode_access_token(token=token)
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(detail="Unauthorized")
    except InvalidTokenError:
        raise UnauthorizedException("Could not validate credentials")
    user = get_user_by_id(user_id=user_id, session=session )
    if user is None:
        raise UnauthorizedException(detail="Unauthorized")
    return user


"""async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["me"])],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user"""