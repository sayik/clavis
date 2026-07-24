from sqlalchemy import DateTime, String, Boolean, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timedelta, UTC
import uuid


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email_verified: Mapped[str] = mapped_column(Boolean, default=False)
    temp_token: Mapped[str] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    notes: Mapped[list["Note"]] = relationship(back_populates="users", cascade="all")
    verification_tokens: Mapped[list["EmailVerificationToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    users: Mapped["User"] = relationship(back_populates="notes")
    files: Mapped[list["File"]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    note_id: Mapped[str] = mapped_column(ForeignKey("notes.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    note: Mapped["Note"] = relationship(back_populates="files")


class PendingDeletion(Base):
    __tablename__ = "pending_deletions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )

    note_id: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String)

    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, processing, completed, failed

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC) + timedelta(minutes=20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="email_verification_tokens")
