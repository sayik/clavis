from datetime import UTC, datetime, timedelta
from enum import StrEnum
import hashlib
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from typing import Any

from ..exception import UnauthorizedException
from ..config.settings import get_settings


settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_token(token: str) -> str:
    """
    Handles hashing of refresh token and stores in db
    - It specifically uses deterministic hashing, """
    return hashlib.sha256(token.encode()).hexdigest()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


TOKEN_EXPIRY = {
    TokenType.ACCESS: timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    TokenType.REFRESH: timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
}


def create_token(user_id: str, token_type: TokenType) -> str:
    payload = {
        "sub": user_id,
        "type": token_type,
        "exp": datetime.now(UTC) + TOKEN_EXPIRY[token_type],
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, token_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except (InvalidTokenError, ExpiredSignatureError):
        raise UnauthorizedException(detail="Invalid token")

    if payload.get("type") != token_type:
        raise UnauthorizedException("Invalid token type.")

    return payload


def create_access_token(user_id: str) -> str:
    return create_token(user_id, TokenType.ACCESS)


def create_refresh_token(user_id: str) -> str:
    return create_token(user_id, TokenType.REFRESH)


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, TokenType.ACCESS)


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, TokenType.REFRESH)