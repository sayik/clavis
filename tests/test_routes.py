from unittest.mock import patch
import io
import pytest
from sqlalchemy.orm import select

from app.db.model_notes import Note, User, File, PendingDeletion
from conftest import TestingSession
from datetime import datetime


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_get_notes(client):
    response = client.get("/notes/")

    assert response.status_code == 200


def test_create_note(client):
    response = client.post(
        "/notes/",
        data={
            "title": "My Note",
            "text": "Hello World",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "My Note"
    assert "id" in data


@patch("main.create_presigned_url")
@patch("main.save_file")
def test_create_note_with_file(
    mock_save_file,
    mock_presigned,
    client,
):
    mock_save_file.return_value = {
        "unique_file_name": "test.png",
        "file_url": "s3://bucket/test.png",
    }

    mock_presigned.return_value = "https://example.com/upload"

    response = client.post(
        "/notes/",
        data={
            "title": "Image Note",
            "text": "contains image",
            "in_file_size": 123,
        },
        files={
            "in_file": (
                "test.png",
                io.BytesIO(b"fake image"),
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Image Note"

    mock_save_file.assert_called_once()


@pytest.mark.asyncio
async def test_file_record_created():
    async with TestingSession() as session:
        result = await session.execute(select(File))

        files = result.scalars().all()

        assert len(files) == 1

        assert files[0].file_name == "test.png"


def test_archive_note(client, sample_note):
    response = client.patch(f"/notes/{sample_note.id}/archive")

    assert response.status_code == 200
    assert response.json() == {"message": "Note archived"}


def test_archive_missing_note(client):
    response = client.patch("/notes/does-not-exist/archive")

    assert response.status_code == 404


def test_move_note_to_recycle_bin(
    client,
    sample_note,
):
    response = client.delete(f"/notes/{sample_note.id}")

    assert response.status_code == 200

    assert response.json() == {"message": "Moved to recycle bin"}


@pytest.mark.asyncio
async def test_recycle_bin_returns_deleted_notes(
    client,
):
    async with TestingSession() as session:
        note = Note(
            id="deleted-note",
            title="Deleted",
            content="content",
            user_id=1,
            deleted_at=datetime.utcnow(),
        )

        session.add(note)
        await session.commit()

    response = client.get("/recycle-bin")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == "deleted-note"


@pytest.mark.asyncio
async def test_restore_note(client):
    async with TestingSession() as session:
        note = Note(
            id="restore-note",
            title="Restore",
            content="content",
            user_id=1,
            deleted_at=datetime.utcnow(),
        )

        session.add(note)
        await session.commit()

    response = client.post("/notes/restore-note/restore")

    assert response.status_code == 200

    assert response.json() == {"message": "Note restored"}

    async with TestingSession() as session:
        restored = await session.get(
            Note,
            "restore-note",
        )

        assert restored.deleted_at is None


@pytest.mark.asyncio
async def test_deleted_notes_not_visible_in_notes_list(
    client,
):
    async with TestingSession() as session:
        active = Note(
            id="active",
            title="Active",
            content="A",
            user_id=1,
        )

        deleted = Note(
            id="deleted",
            title="Deleted",
            content="B",
            user_id=1,
            deleted_at=datetime.utcnow(),
        )

        session.add_all([active, deleted])
        await session.commit()

    response = client.get("/notes/")

    assert response.status_code == 200

    ids = {note["id"] for note in response.json()}

    assert "active" in ids
    assert "deleted" not in ids
