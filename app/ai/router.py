from fastapi import APIRouter

from app.integtation.nova_micro import extract_clinical_data
from app.integration.report_generator import generate_report


router = APIRouter()


@router.post("/scribe")
def create_report(transcript: str):

    clinical_data = extract_clinical_data(transcript)

    report = generate_report(clinical_data)

    return {
        "clinical_data": clinical_data,
        "report": report,
    }

"""AI live suggestion on available medicines- use vector db for that"""
"""Also treatment protocol can use vector db"""
"""Ask AI to design correct treatment course and Include all necessary treatment details"""
"""Return data to frontend"""
"""Send data to pdf maker, with correct formattring"""
"""Send data to database"""
"""Send data """