from .bedrock import converse
from .models import CLAUDE_HAIKU


async def generate_report(clinical_data: str) -> str:

    return await converse(
        model_id=CLAUDE_HAIKU,
        system_prompt="""
You are a medical documentation assistant.

Generate a clinical report from the supplied
clinical information.

Do not add information that was not provided.
""",
        prompt=clinical_data,
        max_tokens=2000,
        temperature=0,
    )