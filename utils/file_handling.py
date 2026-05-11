from fastapi import HTTPException
import aiofiles
import uuid
import os


files_dir = "files"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
data = {}

async def save_file(in_file):
    extension = in_file.filename.split(".")[-1]
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    unique_id = uuid.uuid4().hex
    file_path = os.path.join(files_dir, f"{unique_id}.{extension}")

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await in_file.read()
        await out_file.write(content)

    data["file_url"] = file_path
    data["file_size"] = len(content)
    return data
