from fastapi import FastAPI, UploadFile, HTTPException, status, Depends, Form
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import aiofiles
import os
import uuid

from utils.hash_password import hash_password
from schemas.core import NoteBase, NoteCreate, as_form
from schemas.auth import UserOut, UserSignup
from auth import get_current_username
from db.init_db import get_db
from db.model_notes import User, Note, File


app = FastAPI(dependencies=[Depends(get_current_username)])

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
"""


"""
So the get list of items path and file path can be different can't it be? 
-Your notes object stores objects with different "shapes". Is there a way to map them better? 
You have a Note schema, could you extend that in some way?

re: #2 and #3
If you think about question #2 and the possible ways to fix it, you're going to need to either change how data is stored and/or how it's accessed. 
Is a `dict` the right way to store the data? Compare with how a database would store it. In tables with an integer primary key, 
databases usually track with a "sequence" that will always give you the _next_ number to use. You could use something like that. 
You could also use a UUID, but then you need to think about how to sort items. Do you want to show them in the order created by default?


Since you're using pydantic, you can think through whether you want to use different schemas for the different kinds of notes, 
one schema that could hold all the fields, or whether the note "metadata" (e.g. title, creation timestamp) is stored separately from the note content. 
Could you have a note with text *and* a file? Could you have a note with multiple files?

"""


@app.get("/")
async def health():
    return "Server running"


@app.get("/notes/")
async def request_all_notes():
    return notes

@app.get("/specificnote/")
async def specific_note():
    pass


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
    username: Annotated[str, Depends(get_current_username)],
    in_file: UploadFile | None = None,
):
    result = await session.execute(
        select(User).where(User.name == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    

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
            note_id=new_note.id,  # now available
            file_name=in_file.filename,
            file_url=file_path,
            file_size=len(content),
        )
        session.add(new_file)

    new_note_id = new_note.id
    await session.commit()

    return {"note_id": new_note_id}



@app.delete("/remove/{id}")
async def remove_item(id: int):
    if not id < notes.__len__():
        raise HTTPException(status_code=400, detail="Item not found")
    item = notes.pop(id)
    return {"item": item}
