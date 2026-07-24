from fastapi import FastAPI, UploadFile, HTTPException, status, Depends, Form, Body
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware

from app.exception import BadRequestException
from app.utils.hash_password import hash_password
from app.utils.file_handling import save_file
from app.utils.presigned_url import create_presigned_url
from app.utils.settings import settings
from app.utils.s3_delete_object import delete_objects
from app.schemas.core import NoteBase, NoteCreate, as_form, BulkDeleteIDs
from app.schemas.auth import UserOut, UserSignup
from app.auth import get_current_user
from app.db.init_db import get_db
from app.db.model_notes import User, Note, File
from app.schemas.responses import (
    NoteResponse,
    NoteCreateResponse,
    MessageResponse,
    SignupResponse,
    UpdateResponse,
    DeleteNoteResponse,
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


@app.post("/auth/register", response_model=SignupResponse)
async def register(session: Annotated[AsyncSession, Depends(get_db)], user: Annotated[UserSignup, Form()]):
    #check if credentials already in the db
    # store username and hashed password to db
    # create temporary token 
    # send email to the person to verify it
    # send MFA phone code
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


"""
@app.post("/auth/login", response_model=LoginResponse)
async def login():
    pass


@app.post("/auth/refresh", response_model=RefreshResponse)
async def refresh():
    pass


@app.post("/auth/logout", response_model=LogoutResponse)
async def logout():
    pass


@app.post("/auth/verify-email", response_model=VerifyemailResponse)
async def verify_email():
    pass


@app.post("/auth/resend-verification", response_model=ResendverificationResponse)
async def resend_verification():
    pass
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
