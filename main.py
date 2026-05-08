from fastapi import FastAPI, UploadFile, HTTPException, status, Depends, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import aiofiles
import os
import uuid

from utils.hash_password import hash_password
from schemas.core import NoteBase, NoteCreate, as_form
from schemas.auth import UserOut, UserSignup
from auth import get_current_user
from db.init_db import get_db
from db.model_notes import User, Note, File


app = FastAPI()

notes: dict = {}

files_dir = "files"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


##TODO
"""
- Dockerize !
- Add Database 
- Could you make it so that adding a new note uses a single endpoint, regardless of the "type" (text vs. file)?
- Add auth as a requirement for all the endpoints. Can you limit it so each user only can only interact with their own notes?
- Separate your app into multiple files, e.g. schemas, routes, data access layer, ...
- Delete note
- don't handle hashing
- tests

----- re: #3, Most RESTful APIs will have URLs like
        POST /notes (create)
        GET /notes (list)
        GET /notes/{note_id} (detail)
        PUT/PATCH /notes/{note_id} (update)
        DELETE /notes/{note_id} (delete)

        Additional note-specific "actions" usually take the form of
        POST /notes/{note_id}/action-name

----- Ah I see it now, I'll make the get_current_user return the User object instead of username itself. So the route functions can directly access user id and other information.
----- Will do response_models.

----- re: #4 yes, OAuth2 is a great way to let people log in with accounts they already have
"""


@app.get("/")
async def health():
    return "Server running"


@app.get("/notes/")
async def request_all_notes(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):

    result = await session.execute(
        select(Note).where(Note.user_id == user.id).options(selectinload(Note.files))
    )
    notes = result.scalars().all()

    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "created_at": note.created_at,
            "files": [
                {
                    "file_name": f.file_name,
                    "file_size": f.file_size,
                    "file_url": f.file_url,
                }
                for f in note.files
            ],
        }
        for note in notes
    ]


@app.get("/specificnote/")
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
    need a way to repond to file request
    """
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at,
        "files": [
            {
                "file_name": f.file_name,
                "file_size": f.file_size,
                "file_url": f.file_url,
            }
            for f in note.files
        ],
    }


@app.post("/signup/", response_model=None)
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
    return {"user": user}


@app.post("/notes/")
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
        extension = in_file.filename.split(".")[-1]

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file extension")

        unique_id = uuid.uuid4().hex
        file_path = os.path.join(files_dir, f"{unique_id}.{extension}")

        async with aiofiles.open(file_path, "wb") as out_file:
            content = await in_file.read()
            await out_file.write(content)

        new_file = File(
            note_id=new_note.id,
            file_name=in_file.filename,
            file_url=file_path,
            file_size=len(content),
        )
        session.add(new_file)

    new_note_id = new_note.id
    await session.commit()

    return {"note_id": new_note_id}


@app.delete("/remove/{id}")
async def remove_item(id: int, username: Annotated[str, Depends(get_current_user)]):
    if not id < notes.__len__():
        raise HTTPException(status_code=400, detail="Item not found")
    item = notes.pop(id)
    return {"item": item}
