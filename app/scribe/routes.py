from fastapi import APIRouter, Depends, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, select
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..auth.dependencies import get_current_user
from app.integration.s3_delete_object import delete_objects
from app.exception import( 
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    UnprocessableEntityException,
    InternalServerException,
)
from .file_handling import save_file
from app.integration.presigned_url import create_presigned_url
from app.config.settings import get_settings
from app.db.init_db import get_db
from app.db.models import (
    User,
    Note,
    File,
    )
from app.schemas.auth import UserSignup
from app.schemas.core import NoteCreate, as_form, BulkDeleteIDs
from app.schemas.responses import (
    NoteResponse,
    NoteCreateResponse,
    MessageResponse,
    SignupResponse,
    UpdateResponse,
    DeleteNoteResponse,
    LoginResponse,
    ClinicalNote,
)
from app.scribe.dependency import get_scribe_service


settings = get_settings()

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get("/notes/", response_model=list[NoteResponse])
async def request_all_notes(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    result = await session.execute(
        select(Note)
        .where(
            Note.user_id == user.id,
            Note.deleted_at.is_(None),
            Note.archived_at.is_(None),
        )
        .options(selectinload(Note.files))
    )
    # needs pagination
    notes = result.scalars().all()

    return notes


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def specific_note(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    file: bool = False,
):
    result = await session.execute(
        select(Note)
        .where(
            Note.id == note_id,
            Note.deleted_at.is_(None),
            Note.user_id == user.id,
        )
        .options(selectinload(Note.files))
    )
    note = result.scalar_one_or_none()

    if not note:
        raise NotFoundException(detail="Note not found")

    """
    need a way to respond to file request
    """
    return note


## SEND FILES
@router.get("/notes/files/{file_name}", response_model=None)
async def file_response(
    file_name: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    # if user and file_name:
    #     download_link = create_presigned_url(
    #         file_name=file_name, method="GET", expiration=4600
    #     )
    #     return {"download_link": download_link}
    # else:
    #     raise HTTPException(status_code=400, detail="unauthorized to access")
    """I tend to use this sort of "early return" for various special cases as well as validation,
    so that the main part of the function can know that those cases have been handled."""
    if not (user and file_name):
        raise BadRequestException(detail="unauthorized to access")
    download_link = create_presigned_url(
        file_name=file_name, method="GET", expiration=4600
    )
    return {"download_link": download_link}


@router.post("/notes/", response_model=NoteCreateResponse)
async def create_note(
    note: Annotated[NoteCreate, Depends(as_form)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    in_file: UploadFile | None = None,
    in_file_size: int | None = None,
):
    new_note = Note(
        title=note.title,
        content=note.text,
        user_id=user.id,
    )

    session.add(new_note)

    await session.flush()

    """Here get a presigned url based on the filename, then add it to the route"""
    if in_file:
        file_data = save_file(in_file)

        add_new_file = File(
            note_id=new_note.id,
            file_name=file_data["unique_file_name"],
            file_url=file_data["file_url"],
            file_size=in_file_size,
        )
        session.add(add_new_file)

    pre_signed_url_put = create_presigned_url(
        file_name=file_data["unique_file_name"], method="PUT"
    )

    new_note_data = NoteCreateResponse(
        id=new_note.id,
        title=new_note.title,
        created_at=new_note.created_at,
        pre_signed_url=pre_signed_url_put,
    )
    await session.commit()

    return new_note_data


## NEED TO DO UPDATE Individual NOTES
@router.patch("/notes/{note_id}", response_model=UpdateResponse)
async def update_note(
    note_id: str,
    note: Annotated[NoteCreate, Depends(as_form)],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    in_file: UploadFile | None = None,
    in_file_size: int | None = None,
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
        raise NotFoundException(detail="Note not found")

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
            file_name=file_data["unique_file_name"],
            file_url=file_data["file_url"],
            file_size=in_file_size,
        )

        session.add(new_file)

    await session.commit()
    pre_signed_url_put = create_presigned_url(
        file_name=file_data["unique_file_name"], method="PUT"
    )

    return UpdateResponse(
        message="Note updated successfully", pre_signed_url=pre_signed_url_put
    )


## Bulk delete notes
@router.delete("/notes/", response_model=MessageResponse)
async def bulk_delete(
    data: BulkDeleteIDs,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    if not data.removable:
        raise BadRequestException(status_code=400, detail="No note IDs provided")

    existing = await session.scalars(
        select(Note.id).where(Note.id.in_(data.removable), Note.user_id == user.id)
    )

    existing_ids = existing.all()

    if len(set(existing_ids)) != len(set(data.removable)):
        raise NotFoundException(status_code=404, detail="Matching notes not found")

    remove_files = await session.execute(
        select(File.file_name).where(File.note_id.in_(data.removable))
    )

    items: list[str] = remove_files.scalars().all()

    await session.execute(
        delete(Note).where(Note.id.in_(data.removable), Note.user_id == user.id)
    )

    await session.commit()

    await run_in_threadpool(
        delete_objects,
        items,
    )

    return MessageResponse(message="Notes deleted")


## individual delete
@router.delete("/notes/{note_id}", response_model=DeleteNoteResponse)
async def remove_item(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    remove_files = await session.execute(
        select(File.file_name).where(File.note_id == note_id)
    )

    items = remove_files.scalars().all()

    await session.execute(
        delete(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
        )
    )

    await session.commit()

    result = await run_in_threadpool(
        delete_objects,
        items,
    )

    return DeleteNoteResponse(message="file deleted", details=result)


"""Permanent delete, archive, recycle bin
Deletion could fail midway if db call fails, create a table for stuffs to be deleted"""


@router.patch("/notes/{note_id}/archive")
async def archive_note(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    note = await session.scalar(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
            Note.deleted_at.is_(None),
        )
    )

    if not note:
        raise NotFoundException(404, "Note not found")

    note.archived_at = datetime.utcnow()

    await session.commit()

    return {"message": "Note archived"}


@router.delete("/notes/{note_id}")
async def move_to_recycle_bin(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    note = await session.scalar(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
            Note.deleted_at.is_(None),
        )
    )

    if not note:
        raise NotFoundException(404, "Note not found")

    note.deleted_at = datetime.utcnow()

    await session.commit()

    return {"message": "Moved to recycle bin"}


@router.get("/recycle-bin", response_model=list[NoteResponse])
async def recycle_bin(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    result = await session.execute(
        select(Note)
        .where(
            Note.user_id == user.id,
            Note.deleted_at.is_not(None),
        )
        .options(selectinload(Note.files))
    )

    return result.scalars().all()


@router.post("/notes/{note_id}/restore")
async def restore_note(
    note_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    note = await session.scalar(
        select(Note).where(
            Note.id == note_id,
            Note.user_id == user.id,
            Note.deleted_at.is_not(None),
        )
    )

    if not note:
        raise NotFoundException(404, "Deleted note not found")

    note.deleted_at = None

    await session.commit()

    return {"message": "Note restored"}



@router.post("/notes/{note_id}/scribe", response_model=ClinicalNote)
async def create_scribe(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """So the route is to request already entered clinical data to be processed by AI, input is User_id ie clinic ID   """

    """Call items from s3 and pass it onto AI service so it returns data, put all this into background task"""
    """call db for notes and files for the AI to process"""

    return await get_scribe_service.process(
        notes=notes,
        audio=audio,
        images=images,
    )
