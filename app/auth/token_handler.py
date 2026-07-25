from datetime import UTC, datetime, timedelta
import hashlib
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from ..exception import BadRequestException

from ..utils.settings import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError:
        raise BadRequestException(detail="Token has expired")
    except InvalidTokenError:
        raise BadRequestException(detail="Invalid token")


def hash_token(token: str) -> str:
    """
    Does handle hashing of refresh token
    - It specifically uses deterministic hashing"""
    return hashlib.sha256(token.encode()).hexdigest()

def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "type": "access",
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)