from app.auth.password_handler import verify_password, get_password_hash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exception import UnauthorizedException, InternalServerException
from app.db.models import User
from ..schemas.auth import UserSignup
from ..exception import EmailAlreadyExists, UsernameAlreadyTaken

async def get_user_by_id(session: AsyncSession, user_id: str):
    user = await session.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise UnauthorizedException(detail="User not found")

    return user

async def authenticate_user(session: AsyncSession, username: str, password: str):
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
    pass


async def create_user(
    session: AsyncSession,
    user: UserSignup,
) -> tuple[User, str]:
    """Create the user and verification token."""

    password_hash = get_password_hash(user.password)

    new_user = User(
        email=user.email,
        name=user.username,
        password_hash=password_hash,
    )

    session.add(new_user)
    await session.flush()

    return new_user


async def validate_user_signup(
    session: AsyncSession,
    user: UserSignup,
) -> None:
    """Raise an exception if the email or username is already in use."""

    result = await session.execute(
        select(User).where(User.email == user.email)
    )
    existing_email = result.scalar_one_or_none()

    if existing_email:
        raise EmailAlreadyExists(user.email)

    result = await session.execute(
        select(User).where(User.name == user.username)
    )
    existing_username = result.scalar_one_or_none()

    if existing_username:
        raise UsernameAlreadyTaken(user.username)