from fastapi import HTTPException
import uuid


files_dir = "files"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
data = {}
MAX_SIZE = 10 * 1024 * 1024
size = 0

def save_file(in_file):
    extension = in_file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")

    unique_id = uuid.uuid4().hex
    unique_file_name = f"{unique_id}.{extension}"

    data["file_url"] = "Stored in cloud s3"
    data["unique_file_name"] = unique_file_name
    """
    Needs to send file name to db and pre-signed url"""
    return data
