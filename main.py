from fastapi import FastAPI, Body,File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Annotated
from pydantic import BaseModel
import aiofiles
import os
import  uuid

from auth import get_current_username


app = FastAPI(dependencies=[Depends(get_current_username)])

notes: dict = {}

files_dir = "files"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


##TODO
"""
- Dockerize
- Add Database 
"""


"""Everything goes into a dictionary, so response is ordered and annotated. 

And in response the frontend will query what it needs when it comes to files and images.


So the get list of items path and file path can be different can't it be? """

class Note(BaseModel):
    title: str
    text: str | None = None



@app.get("/")
async def health():
    return "Server running" 


@app.get("/notes")
async def request_all_notes():
    return notes


@app.post("/notes")
async def note_text(username: Annotated[str, Depends(get_current_username)], note: Note):
    notes_count = notes.__len__()
    notes[notes_count + 1] = {"title":note.title, "text":note.text}
    return (username, note)


@app.post("/files/")
async def create_file(in_file: UploadFile):
    notes_count = notes.__len__()
    unique_id = uuid.uuid4().hex
    extension = in_file.filename.split(".")[-1]
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    async with aiofiles.open(os.path.join(files_dir, f"{unique_id}.{extension}"), 'wb') as out_file:
        notes[notes_count + 1] = {extension, os.path.join(files_dir, f"{unique_id}.{extension}")}
        content = await in_file.read()  # async read
        await out_file.write(content)  # async write
    return {"file_size": in_file.size}

##front end calls for files to this end point, send in number or the file hash. 
@app.post("/requestfile")
async def request_file():
    pass

@app.delete("/remove")
async def remove_item(id: int):
    pass
