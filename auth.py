from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Annotated
import secrets

security = HTTPBasic()


async def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    """
    HTTP Basic authentication.

    [HTTP Basic Auth] The browser itself typically caches the credentials
    for the duration of the session and automatically re-sends them in the
    Authorization header on subsequent requests — so the login prompt usually
    only appears once per browser session, not on every request. However, this is
    browser behavior, not something HTTPBasic or FastAPI controls directly.
    """

    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = b"stanley"
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = b"sword"
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
