from fastapi import FastAPI, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Annotated
import aiofiles
import os
import uuid

from schemas.core import NoteBase, NoteCreate, as_form
from auth import get_current_username


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


@app.post("/notes/")
async def create_note(
    note: Annotated[NoteCreate, Depends(as_form)], in_file: UploadFile | None = None
):
    notes_count = notes.__len__()
    if in_file:
        unique_id = uuid.uuid4().hex
        extension = in_file.filename.split(".")[-1]
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file extension")
        async with aiofiles.open(
            os.path.join(files_dir, f"{unique_id}.{extension}"), "wb"
        ) as out_file:
            notes[notes_count + 1] = {
                "file": True,
                "location": os.path.join(files_dir, f"{unique_id}.{extension}"),
            }
            content = await in_file.read()  # async read
            await out_file.write(content)  # async write
        return {"file_size": in_file.size, "note": note}
    else:
        return {"note": note}


##front end calls for files to this end point, send in number or the file hash.
@app.post("/requestfile/{filenumber}")
async def request_file(filenumber: int):
    if not filenumber < notes.__len__():
        raise HTTPException(status_code=400, detail="Item not found")
    if notes[filenumber]["file"]:
        return FileResponse(notes[filenumber]["location"])
    else:
        raise HTTPException(status_code=400, detail="Item not found")


@app.delete("/remove/{id}")
async def remove_item(id: int):
    if not id < notes.__len__():
        raise HTTPException(status_code=400, detail="Item not found")
    item = notes.pop(id)
    return {"item": item}
