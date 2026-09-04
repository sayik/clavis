from functools import lru_cache

from app.ai.openai_client import OpenAIClient
from app.scribe.service import ScribeService

"""Cache instance call avoiding expiration"""


@lru_cache
def get_openai_client() -> OpenAIClient:
    return OpenAIClient()


def get_scribe_service() -> ScribeService:
    return ScribeService(ai_client=get_openai_client())
