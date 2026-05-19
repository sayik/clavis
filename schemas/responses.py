from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FileResponseSchema(BaseModel):
    file_name: str
    file_size: int
    file_url: str

    #here db object can be directly passed to the Model
    model_config = ConfigDict(from_attributes=True)


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str | None
    created_at: datetime
    files: list[FileResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)


class NoteCreateResponse(BaseModel):
    id: str
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class SignupResponse(BaseModel):
    username: str
    email: str
