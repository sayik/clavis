from fastapi import FastAPI, UploadFile, HTTPException, status, Depends, Form, Body
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware

from app.exception import BadRequestException
from app.auth.integrate import get_current_user
from app.auth.routes import router as auth_router
from app.scribe.routes import router as case_router

from app.config.settings import settings
from app.schemas.core import NoteBase, NoteCreate, as_form, BulkDeleteIDs
from app.schemas.auth import UserOut, UserSignup
from app.db.init_db import get_db
from app.db.models import (
    User,
    Note,
    File,
    EmailVerificationToken,
    RefreshToken,
    PasswordResetToken,
)

from app.schemas.responses import (
    NoteResponse,
    NoteCreateResponse,
    MessageResponse,
    SignupResponse,
    UpdateResponse,
    DeleteNoteResponse,
)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"),
    allow_headers=settings.CORS_HEADERS,
)

app.include_router(auth_router)
app.include_router(case_router)

##TODO
"""
- FileResponse ✔️
- Dockerize ! ✔️
- Add Database ✔️
- Could you make it so that adding a new note uses a single endpoint, regardless of the "type" (text vs. file)? ✔️
- Add auth as a requirement for all the endpoints. Can you limit it so each user only can only interact with their own notes? ✔️
- Separate your app into multiple files, e.g. schemas, routes, data access layer, ... ✔️
- Delete note ✔️
- don't handle hashing ✔️
- incoming file size handling 
- tests ✔️
- Isolate user ie  user access + Bytecode + multistage build in dockerfile
- Frontend
- logging 
- ADD AI feature 
- Pre-commit - ✔️
- s3 presigned for images ✔️

"""
@app.get("/health")
async def health_check():
    return {"Health": "success"}