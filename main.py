from fastapi import FastAPI, UploadFile, HTTPException, status, Depends, Form, Body
from fastapi.responses import FileResponse
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from utils.hash_password import hash_password
from utils.file_handling import save_file
from utils.presigned_url import create_presigned_url
from schemas.core import NoteBase, NoteCreate, as_form, BulkDeleteIDs
from schemas.auth import UserOut, UserSignup
from auth import get_current_user
from db.init_db import get_db
from db.model_notes import User, Note, File
from schemas.responses import (
    NoteResponse,
    NoteCreateResponse,
    MessageResponse,
    SignupResponse,
)


app = FastAPI()

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
- incoming file size handling - by the time uploadfile passes the data to route function it's already in 
    the temp storage. This needs to be handled at the reverse proxy
- tests
- Isolate user ie  user access + Bytecode + multistage build in dockerfile
- Frontend
- logging 
- Pre-commit
- s3 presigned for images

--Done--- re: #3, Most RESTful APIs will have URLs like
        POST /notes (create)
        GET /notes (list)
        GET /notes/{note_id} (detail)
        PUT/PATCH /notes/{note_id} (update)
        DELETE /notes/{note_id} (delete)

        Additional note-specific "actions" usually take the form of
        POST /notes/{note_id}/action-name
----> Uniform design of routes and endpoints

--Done--- Ah I see it now, I'll make the get_current_user return the User object instead of username itself. So the route functions can directly access user id and other information.
--Done--- Will do response_models.

----- re: #4 yes, OAuth2 is a great way to let people log in with accounts they already have
----- Cascade delete images/audio that was deleted from db
"""


@app.get("/health")
async def health():
    return "Server running"


@app.get("/notes/", response_model=list[NoteResponse])
async def request_all_notes(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    result = await session.execute(
        select(Note).where(Note.user_id == user.id).options(selectinload(Note.files))
    )
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
        .where(Note.id == note_id, Note.user_id == user.id)
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
@app.get("/notes/files/{file_id}", response_model=None)
async def file_response(
    file_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    result = await session.execute(select(File).where(File.id == file_id))
    # return file_response(result.file)
    # result is the filename with uuid, now send the uuid(filename), method and needed arguments for pre-signed s3 bucket
    download_link = create_presigned_url(object_name=result, method="GET", expiration=4600)



@app.post("/signup/", response_model=SignupResponse)
async def signup(
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[UserSignup, Form()],
):
    result = await session.execute(select(User).where(User.email == user.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
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


@app.post("/notes/", response_model=NoteBase)
async def create_note(
    note: Annotated[NoteCreate, Depends(as_form)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    in_file: UploadFile | None = None,
):
    new_note = Note(
        title=note.title,
        content=note.text,
        user_id=user.id,
    )

    session.add(new_note)

    await session.flush()

    if in_file:
        file_data = await save_file(in_file)

        add_new_file = File(
            note_id=new_note.id,
            file_name=in_file.filename,
            file_url=file_data["file_url"],
            file_size=file_data["file_size"],
        )
        session.add(add_new_file)

    new_note_data = NoteBase(title=new_note.title, created_at=new_note.created_at)
    await session.commit()

    return new_note_data


## NEED TO DO UPDATE Individual NOTES
@app.patch("/notes/{note_id}", response_model=MessageResponse)
async def update_note(
    note_id: str,
    note: Annotated[NoteCreate, Depends(as_form)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    in_file: UploadFile | None = None,
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
            file_name=in_file.filename,
            file_url=file_data["file_url"],
            file_size=file_data["file_size"],
        )

        session.add(new_file)

    await session.commit()

    return MessageResponse(message="Note updated successfully")


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

    await session.execute(
        delete(Note).where(Note.id.in_(data.removable), Note.user_id == user.id)
    )

    await session.commit()

    return MessageResponse(message="Notes deleted")


## individual delete
@app.delete("/notes/{note_id}", response_model=MessageResponse)
async def remove_item(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    await session.execute(
        delete(Note).where(Note.id == note_id, Note.user_id == user.id)
    )
    await session.commit()

    return MessageResponse(message="Note deleted")
