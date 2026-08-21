from typing import Any

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas.responses import ClinicalNote


class OpenAIClient:
    def __init__(self) -> None:
        settings = get_settings()

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

        self.model = settings.openai_model
        self.transcription_model = settings.openai_transcription_model

    async def transcribe(self, audio_file: Any) -> str:
        response = await self.client.audio.transcriptions.create(
            model=self.transcription_model,
            file=audio_file,
        )

        return response.text

    async def generate(
        self,
        *,
        instructions: str,
        content: list[dict],
    ):
        response = await self.client.responses.parse(
            model=self.model,
            instructions=instructions,
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
            text_format=ClinicalNote,
        )

        return response.output_parsed