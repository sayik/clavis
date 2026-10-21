from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.db.models import User


router = APIRouter(
    prefix="/diagnoses",
    tags=["diagnoses"],
)


COMMON_DIAGNOSES = [
    {
        "id": "diag_001",
        "code": "I10",
        "coding_system": "ICD-10",
        "name": "Essential hypertension",
    },
    {
        "id": "diag_002",
        "code": "E11.9",
        "coding_system": "ICD-10",
        "name": "Type 2 diabetes mellitus without complications",
    },
    {
        "id": "diag_003",
        "code": "J06.9",
        "coding_system": "ICD-10",
        "name": "Acute upper respiratory infection",
    },
    {
        "id": "diag_004",
        "code": "J40",
        "coding_system": "ICD-10",
        "name": "Bronchitis",
    },
    {
        "id": "diag_005",
        "code": "J18.9",
        "coding_system": "ICD-10",
        "name": "Pneumonia, unspecified organism",
    },
    {
        "id": "diag_006",
        "code": "A90",
        "coding_system": "ICD-10",
        "name": "Dengue fever",
    },
    {
        "id": "diag_007",
        "code": "A01.0",
        "coding_system": "ICD-10",
        "name": "Typhoid fever",
    },
]


@router.get("/common")
async def get_common_diagnoses():
    return {
        "items": COMMON_DIAGNOSES,
        "total": len(COMMON_DIAGNOSES),
    }


@router.get("")
async def search_diagnoses(
    user: Annotated[User, Depends(get_current_user)],
    q: str | None = Query(default=None, min_length=1),
):
    if not q:
        return {
            "items": COMMON_DIAGNOSES,
            "total": len(COMMON_DIAGNOSES),
        }

    query = q.lower()

    results = [
        diagnosis
        for diagnosis in COMMON_DIAGNOSES
        if (query in diagnosis["name"].lower() or query in diagnosis["code"].lower())
    ]

    return {
        "items": results,
        "total": len(results),
    }
