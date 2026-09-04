import base64
from typing import Sequence

from fastapi import UploadFile

from app.ai.openai_client import OpenAIClient
from app.scribe.prompt import SCRIBE_SYSTEM_PROMPT
from app.schemas.responses import ClinicalNote


class ScribeService:
    def __init__(self, ai_client: OpenAIClient):
        self.ai = ai_client

    async def process(
        self,
        *,
        notes: str | None,
        audio: UploadFile | None,
        images: Sequence[UploadFile] | None,
    ) -> ClinicalNote:

        transcript = None

        # --------------------------------
        # 1. Transcribe audio
        # --------------------------------

        if audio is not None:
            audio_bytes = await audio.read()

            transcript = await self.ai.transcribe(
                audio_file=(
                    audio.filename or "audio.wav",
                    audio_bytes,
                    audio.content_type or "audio/wav",
                )
            )

        # --------------------------------
        # 2. Build model input
        # --------------------------------

        content: list[dict] = []

        if notes:
            content.append(
                {
                    "type": "input_text",
                    "text": f"""
CLINICIAN NOTES:

{notes}
""",
                }
            )

        if transcript:
            content.append(
                {
                    "type": "input_text",
                    "text": f"""
CONSULTATION TRANSCRIPT:

{transcript}
""",
                }
            )

        # --------------------------------
        # 3. Add images
        # --------------------------------

        for image in images or []:
            image_bytes = await image.read()

            encoded = base64.b64encode(image_bytes).decode("utf-8")

            media_type = image.content_type or "image/jpeg"

            content.append(
                {
                    "type": "input_image",
                    "image_url": (f"data:{media_type};base64,{encoded}"),
                }
            )

        # --------------------------------
        # 4. Generate clinical note
        # --------------------------------

        result = await self.ai.generate(
            instructions=SCRIBE_SYSTEM_PROMPT,
            content=content,
        )

        return result
