from fastapi import FastAPI, UploadFile, HTTPException, status, Depends, Form, Body
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware

from app.exception import BadRequestException
from app.auth.password_handler import get_password_hash, verify_password
from app.auth.token_handler import (
    create_refresh_token,
    create_access_token,
    hash_token,
    decode_token,
)
from app.utils.file_handling import save_file
from app.utils.presigned_url import create_presigned_url
from app.utils.settings import settings
from app.utils.s3_delete_object import delete_objects
from app.schemas.core import NoteBase, NoteCreate, as_form, BulkDeleteIDs
from app.schemas.auth import UserOut, UserSignup
from app.auth.email_handler import (
    generate_email_verification_link,
    send_verification_email,
)
from app.db.init_db import get_db
from app.db.models import (
    User,
    Note,
    File,
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
)
from app.schemas.responses import (
    NoteResponse,
    NoteCreateResponse,
    MessageResponse,
    SignupResponse,
    UpdateResponse,
    DeleteNoteResponse,
    LoginResponse,
)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

##TODO
"""
- FileResponse ✔️
- Dockerize ! ✔️
- Add Database ✔️
- Could you make it so that adding a new note uses a single endpoint, regardless of the "type" (text vs. file)? ✔️
- Add auth as a requirement for all the endpoints. Can you limit it so each user only can only interact with their own notes? ✔️
- Separate your app into multiple files, e.g. schemas, routes, data access layer, ... ✔️
- Delete note ✔️
- don't handle hashing ✔️
- incoming file size handling 
- tests ✔️
- Isolate user ie  user access + Bytecode + multistage build in dockerfile
- Frontend
- logging 
- ADD AI feature 
- Pre-commit - ✔️
- s3 presigned for images ✔️

"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/health")
async def health(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


"""

POST /auth/password/forgot
POST /auth/password/reset

POST /auth/verify-email
POST /auth/resend-verification
"""


@app.get("/auth/me", response_model=UserOut)
async def me(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    # here get current user can check for valid token or return exception
    return user


@app.post("/auth/signup", response_model=SignupResponse)
async def register(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserSignup, Form()],
):
    result = await session.execute(select(User).where(User.email == user.email))
    existing = result.scalar_one_or_none()

    if existing:
        return JSONResponse(
            status_code=409,
            content={
                "error": "email_exists",
                "email": user.email,
                "redirect_to": "/login",
            },
        )

    if existing.name:
        raise BadRequestException(detail=f"Username {existing.name} already taken")

    password_hash = get_password_hash(user.password)
    new_user = User(email=user.email, name=user.username, password_hash=password_hash)
    session.add(new_user)

    verification = generate_email_verification_link(settings.FRONTEND_URL)

    # Store only the hash
    verification_token = EmailVerificationToken(
        user_id=new_user.id,
        token_hash=verification.token_hash,
    )

    session.add(verification_token)

    # Email the link
    await send_verification_email(
        new_user.email,
        verification.verification_link,
    )
    await session.commit()
    return SignupResponse(username=user.username, email=user.email)


@app.get("/auth/verify-email")
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


@app.post("/auth/login", response_model=LoginResponse)
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


@app.post("/auth/logout", response_model=LogoutResponse)
async def logout(
    logout_request: LogoutRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponse:
    token_hash = hash_token(logout_request.refresh_token)

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


@app.post("/auth/refresh", response_model=RefreshResponse)
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
            RefreshToken.device_id == request.device_id,
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
            device_id=request.device_id,
            token_hash=hash_token(refresh_token),
        )
    )

    await session.commit()

    return RefreshResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@app.post(
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


@app.post("/auth/forgot-password")
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


@app.post("/auth/reset-password")
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
4. Change password (later)

Once you have authentication middleware that gives you the current user, a change-password endpoint is straightforward:

Require a valid access token.
Verify the current password.
Hash and save the new password.
Delete all refresh tokens except optionally the current session.
Return success.

At that point, the authentication system is complete and follows a solid, production-ready pattern.

"""


@app.get("/notes/", response_model=list[NoteResponse])
async def request_all_notes(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    result = await session.execute(
        select(Note)
        .where(
            Note.user_id == user.id,
            Note.deleted_at.is_(None),
            Note.archived_at.is_(None),
        )
        .options(selectinload(Note.files))
    )
    # needs pagination
    notes = result.scalars().all()

    return notes


@app.get("/notes/{note_id}", response_model=NoteResponse)
async def specific_note(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    file: bool = False,
):
    result = await session.execute(
        select(Note)
        .where(
            Note.id == note_id,
            Note.deleted_at.is_(None),
            Note.user_id == user.id,
        )
        .options(selectinload(Note.files))
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    """
    need a way to respond to file request
    """
    return note


## SEND FILES
@app.get("/notes/files/{file_name}", response_model=None)
async def file_response(
    file_name: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    # if user and file_name:
    #     download_link = create_presigned_url(
    #         file_name=file_name, method="GET", expiration=4600
    #     )
    #     return {"download_link": download_link}
    # else:
    #     raise HTTPException(status_code=400, detail="unauthorized to access")
    """I tend to use this sort of "early return" for various special cases as well as validation,
    so that the main part of the function can know that those cases have been handled."""
    if not (user and file_name):
        raise HTTPException(status_code=400, detail="unauthorized to access")
    download_link = create_presigned_url(
        file_name=file_name, method="GET", expiration=4600
    )
    return {"download_link": download_link}


@app.post("/signup/", response_model=SignupResponse)
async def signup(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserSignup, Form()],
):
    result = await session.execute(select(User).where(User.email == user.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        return JSONResponse(
            status_code=409,
            content={
                "error": "email_exists",
                "email": user.email,
                "redirect_to": "/login",
            },
        )

    result = await session.execute(select(User).where(User.name == user.username))
    existing_username = result.scalar_one_or_none()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    password_hash = hash_password(user.password)
    new_user = User(email=user.email, name=user.username, password_hash=password_hash)
    session.add(new_user)
    await session.commit()
    return SignupResponse(username=user.username, email=user.email)


@app.post("/notes/", response_model=NoteCreateResponse)
async def create_note(
    note: Annotated[NoteCreate, Depends(as_form)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    in_file: UploadFile | None = None,
    in_file_size: int | None = None,
):
    new_note = Note(
        title=note.title,
        content=note.text,
        user_id=user.id,
    )

    session.add(new_note)

    await session.flush()

    """Here get a presigned url based on the filename, then add it to the route"""
    if in_file:
        file_data = save_file(in_file)

        add_new_file = File(
            note_id=new_note.id,
            file_name=file_data["unique_file_name"],
            file_url=file_data["file_url"],
            file_size=in_file_size,
        )
        session.add(add_new_file)

    pre_signed_url_put = create_presigned_url(
        file_name=file_data["unique_file_name"], method="PUT"
    )

    new_note_data = NoteCreateResponse(
        id=new_note.id,
        title=new_note.title,
        created_at=new_note.created_at,
        pre_signed_url=pre_signed_url_put,
    )
    await session.commit()

    return new_note_data


## NEED TO DO UPDATE Individual NOTES
@app.patch("/notes/{note_id}", response_model=UpdateResponse)
async def update_note(
    note_id: str,
    note: Annotated[NoteCreate, Depends(as_form)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    in_file: UploadFile | None = None,
    in_file_size: int | None = None,
):
    update_data = {}

    if note.title is not None:
        update_data["title"] = note.title

    if note.text is not None:
        update_data["content"] = note.text

    existing_note = await session.scalar(
        select(Note).where(Note.id == note_id, Note.user_id == user.id)
    )

    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")

    if update_data:
        await session.execute(
            update(Note)
            .where(Note.id == note_id, Note.user_id == user.id)
            .values(**update_data)
        )

    if in_file:
        file_data = await save_file(in_file)

        new_file = File(
            note_id=note_id,
            file_name=file_data["unique_file_name"],
            file_url=file_data["file_url"],
            file_size=in_file_size,
        )

        session.add(new_file)

    await session.commit()
    pre_signed_url_put = create_presigned_url(
        file_name=file_data["unique_file_name"], method="PUT"
    )

    return UpdateResponse(
        message="Note updated successfully", pre_signed_url=pre_signed_url_put
    )


## Bulk delete notes
@app.delete("/notes/", response_model=MessageResponse)
async def bulk_delete(
    data: BulkDeleteIDs,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if not data.removable:
        raise HTTPException(status_code=400, detail="No note IDs provided")

    existing = await session.scalars(
        select(Note.id).where(Note.id.in_(data.removable), Note.user_id == user.id)
    )

    existing_ids = existing.all()

    if len(set(existing_ids)) != len(set(data.removable)):
        raise HTTPException(status_code=404, detail="Matching notes not found")

    remove_files = await session.execute(
        select(File.file_name).where(File.note_id.in_(data.removable))
    )

    items: list[str] = remove_files.scalars().all()

    await session.execute(
        delete(Note).where(Note.id.in_(data.removable), Note.user_id == user.id)
    )

    await session.commit()

    await run_in_threadpool(
        delete_objects,
        items,
    )

    return MessageResponse(message="Notes deleted")


## individual delete
@app.delete("/notes/{note_id}", response_model=DeleteNoteResponse)
async def remove_item(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    remove_files = await session.execute(
        select(File.file_name).where(File.note_id == note_id)
    )

    items = remove_files.scalars().all()

    await session.execute(
        delete(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
        )
    )

    await session.commit()

    result = await run_in_threadpool(
        delete_objects,
        items,
    )

    return DeleteNoteResponse(message="file deleted", details=result)


"""Permanent delete, archive, recycle bin
Deletion could fail midway if db call fails, create a table for stuffs to be deleted"""


@app.patch("/notes/{note_id}/archive")
async def archive_note(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    note = await session.scalar(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
            Note.deleted_at.is_(None),
        )
    )

    if not note:
        raise HTTPException(404, "Note not found")

    note.archived_at = datetime.utcnow()

    await session.commit()

    return {"message": "Note archived"}


@app.delete("/notes/{note_id}")
async def move_to_recycle_bin(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    note = await session.scalar(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
            Note.deleted_at.is_(None),
        )
    )

    if not note:
        raise HTTPException(404, "Note not found")

    note.deleted_at = datetime.utcnow()

    await session.commit()

    return {"message": "Moved to recycle bin"}


@app.get("/recycle-bin", response_model=list[NoteResponse])
async def recycle_bin(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    result = await session.execute(
        select(Note)
        .where(
            Note.user_id == user.id,
            Note.deleted_at.is_not(None),
        )
        .options(selectinload(Note.files))
    )

    return result.scalars().all()


@app.post("/notes/{note_id}/restore")
async def restore_note(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    note = await session.scalar(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
            Note.deleted_at.is_not(None),
        )
    )

    if not note:
        raise HTTPException(404, "Deleted note not found")

    note.deleted_at = None

    await session.commit()

    return {"message": "Note restored"}
