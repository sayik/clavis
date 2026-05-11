from pydantic import BaseModel
from datetime import datetime
from typing import Annotated
from fastapi import Form


class NoteBase(BaseModel):
    title: str
    created_at: datetime


class NoteCreate(NoteBase):
    text: str | None = None


def as_form(
    title: Annotated[str, Form()],
    created_at: Annotated[datetime, Form()],
    text: Annotated[str, Form()] = None,
) -> NoteCreate:
    return NoteCreate(title=title, created_at=created_at, text=text)

class BulkDeleteIDs(BaseModel):
    removable: list[str]

## Response model
