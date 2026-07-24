from password_handler import verify_password, get_password_hash
from sqlalchemy.ext.asyncio import async_session as session


def get_user(db, username: str):
    if username:
        pass
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    """Authenticate a user using a username and password.

    Retrieves the user associated with ``username`` and verifies the
    supplied password against the stored password hash. To reduce the
    effectiveness of username enumeration attacks, a dummy password hash
    is verified when the requested user does not exist.

    Args:
        db: Database session used to retrieve user records.
        username: Username submitted during login.
        password: Plain-text password submitted during login.

    Returns:
        The authenticated ``User`` instance if the credentials are valid,
        otherwise ``None``.

    Security:
        A constant dummy password hash is verified for unknown users to
        reduce observable timing differences between valid and invalid
        usernames.
    """
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_user(get_db: session, username: int, email: str, unhashed_password: str) -> None:
    ## conditionals check input data 
    ## call password hash 
    ## save to the db 