from app.config import settings

"""
- Use web hooks
- Send pre-signed link
"""


async def generate_pdf(doctor_details, patient_details, ):
    
    response =   await pdf_client.post(
    "https://pdf-service.example.com/generate",
    json={
        "job_id": job_id,
        "data": report_data,
        "callback_url": "https://api.example.com/pdf-completed",
    },

    response.raise_for_status()

    return {"job_id": job_id, "status": "processing"}
)