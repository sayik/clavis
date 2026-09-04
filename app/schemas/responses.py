from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FileResponseSchema(BaseModel):
    file_name: str
    file_url: str
    file_size: int | None = None

    # here db object can be directly passed to the Model
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
    pre_signed_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class UpdateResponse(MessageResponse):
    pre_signed_url: str | None = None


class DeleteNoteResponse(MessageResponse):
    details: dict


class SignupResponse(BaseModel):
    username: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ClinicalNote(BaseModel):
    chief_complaint: str | None
    history_of_present_illness: str | None
    examination: str | None
    assessment: list[str]
    plan: list[str]
    medications: list[str]
    investigations: list[str]
    follow_up: str | None

class Medication(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    