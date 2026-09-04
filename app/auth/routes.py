from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.exception import BadRequestException, EmailAlreadyExists, UsernameAlreadyTaken
from app.auth.dependencies import get_current_user
from app.auth.user_handler import create_user, validate_user_signup
from app.auth.password_handler import get_password_hash, verify_password
from app.auth.token_handler import (
    create_refresh_token,
    create_access_token,
    hash_token,
    decode_token,
)
from app.auth.email_handler import generate_email_verification_link, send_verification_email

from app.config.settings import get_settings
from app.schemas.auth import UserOut, UserSignup, ResendVerificationResponse, RefreshResponse
from app.db.init_db import get_db
from app.db.models import (
    User,
    EmailVerificationToken,
    RefreshToken,
    PasswordResetToken,
)
from app.schemas.auth import (
    LogoutRequest,
    ResetPasswordRequest,
    RefreshRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    LogoutResponse,
)
from app.schemas.responses import (
    SignupResponse,
    LoginResponse,
)  


settings = get_settings()
router = APIRouter()


@router.get("/auth/me", response_model=UserOut)
async def me(
    user: Annotated[User, Depends(get_current_user)],
):
    # here get current user can check for valid token or return exception
    return user


@router.post("/auth/signup", response_model=SignupResponse)
async def register(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserSignup, Form()],
):
    try:
        await validate_user_signup(session, user)
    except EmailAlreadyExists as exc:
        return JSONResponse(
            status_code=409,
            content={
                "error": "email_exists",
                "email": exc.email,
                "redirect_to": "/login",
            },
    )
    except UsernameAlreadyTaken as exc:
        raise BadRequestException(
            detail=f"Username '{exc.username}' is already taken."
    )


    new_user = await create_user(session, user)

    verification = generate_email_verification_link(settings.FRONTEND_URL)

    # Store only the hash
    verification_token = EmailVerificationToken(
        user_id=new_user.id,
        token_hash=verification.token_hash,
    )

    session.add(verification_token)
    await session.commit()

    # Email the link
    await send_verification_email(
        new_user.email,
        verification.verification_link,
    )
    return SignupResponse(username=user.username, email=user.email)


@router.get("/auth/verify-email")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_db),
):
    token_hash = get_password_hash(token)

    verification = await session.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )

    if verification is None:
        raise BadRequestException(detail="Invalid token")

    if verification.expires_at < datetime.now():
        await session.delete(verification)
        await session.commit()

        raise BadRequestException("Invalid verification token")

    user = await session.get(User, verification.user_id)

    if user is None:
        raise BadRequestException(detail="User not found")
    user.email_verified = True

    # Remove the token so it cannot be reused
    await session.delete(verification)

    await session.commit()

    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/login?verified=true",
        status_code=302,
    )


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    device_id: Annotated[str, Form()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    user = await session.scalar(select(User).where(User.email == form_data.username))

    if user is None:
        raise BadRequestException(detail="No account exists with this email.")

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise BadRequestException(detail="Incorrect password.")

    if not user.email_verified:
        raise BadRequestException(detail="Please verify your email before logging in.")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Remove any existing refresh token for this device
    existing = await session.scalar(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.device_id == device_id,
        )
    )

    if existing is not None:
        await session.delete(existing)

    session.add(
        RefreshToken(
            user_id=user.id,
            device_id=device_id,
            token_hash=hash_token(refresh_token),
        )
    )

    await session.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/auth/logout", response_model=LogoutResponse)
async def logout(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponse:

    # Access token must be really short TTL so logout works. Take access token and not refresh token and black list aceess and delete refresh token. 
    
    # find user - delete refresh token attached to it 

    db_token = await session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.device_id == logout_request.device_id,
        )
    )

    if db_token is not None:
        await session.delete(db_token)
        await session.commit()

    return LogoutResponse(message="Successfully logged out.")


@router.post("/auth/refresh", response_model=RefreshResponse)
async def refresh(
    refresh_request: RefreshRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RefreshResponse:
    payload = hash_token(refresh_request.refresh_token)

    if payload.get("type") != "refresh":
        raise BadRequestException(detail="Invalid refresh token")

    token_hash = hash_token(refresh_request.refresh_token)

    db_token = await session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.device_id == refresh_request.device_id,
        )
    )

    if db_token is None:
        raise BadRequestException(detail="Refresh token not found")

    if db_token.expires_at < datetime.now(UTC):
        await session.delete(db_token)
        await session.commit()

        raise BadRequestException(detail="Refresh token expired")

    user = await session.get(User, payload["sub"])

    if user is None:
        raise BadRequestException(detail="User not found")

    if not user.email_verified:
        raise BadRequestException(detail="Please verify your email before logging in.")

    # Rotate refresh token
    await session.delete(db_token)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    session.add(
        RefreshToken(
            user_id=user.id,
            device_id=refresh_request.device_id,
            token_hash=hash_token(refresh_token),
        )
    )

    await session.commit()

    return RefreshResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/auth/resend-verification",
    response_model=ResendVerificationResponse,
)
async def resend_verification(
    request: ResendVerificationRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ResendVerificationResponse:
    user = await session.scalar(select(User).where(User.email == request.email))

    if user is None:
        raise BadRequestException(detail="No account exists with this email.")

    if user.email_verified:
        raise BadRequestException(detail="Email is already verified.")

    # Remove previous verification tokens
    tokens = await session.scalars(
        select(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )

    for token in tokens:
        await session.delete(token)

    verification = generate_email_verification_link(settings.FRONTEND_URL)

    session.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=verification.token_hash,
        )
    )

    await send_verification_email(
        user.email,
        verification.verification_link,
    )

    await session.commit()

    return ResendVerificationResponse(message="Verification email sent.")


"""@router.post("/auth/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    user = await session.scalar(select(User).where(User.email == request.email))

    # Always return success to avoid email enumeration.
    if user is None:
        return {"message": "If an account exists, a password reset link has been sent."}

    tokens = await session.scalars(
        select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )

    for token in tokens:
        await session.delete(token)

    reset = generate_password_reset_link(
        settings.FRONTEND_URL,
    )

    session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=reset.token_hash,
        )
    )

    await send_password_reset_email(
        user.email,
        reset.reset_link,
    )

    await session.commit()

    return {"message": "If an account exists, a password reset link has been sent."}


@router.post("/auth/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    token_hash = hash_token(request.token)

    reset = await session.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )

    if reset is None:
        raise BadRequestException(detail="Invalid reset token")

    if reset.expires_at < datetime.now(UTC):
        await session.delete(reset)
        await session.commit()
        raise BadRequestException(detail="Reset token expired")

    user = await session.get(User, reset.user_id)

    if user is None:
        raise BadRequestException(detail="User not found")

    user.password_hash = get_password_hash(request.new_password)

    # Remove the used reset token.
    await session.delete(reset)

    # Log the user out everywhere.
    refresh_tokens = await session.scalars(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )

    for refresh_token in refresh_tokens:
        await session.delete(refresh_token)

    await session.commit()

    return {"message": "Password updated successfully."}

"""



"""
4. Change password (later)

Once you have authentication middleware that gives you the current user, a change-password endpoint is straightforward:

Require a valid access token.
Verify the current password.
Hash and save the new password.
Delete all refresh tokens except optionally the current session.
Return success.

At that point, the authentication system is complete and follows a solid, production-ready pattern.

"""