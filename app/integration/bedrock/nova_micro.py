from .bedrock import converse
from .models import NOVA_MICRO


async def extract_clinical_data(transcript: str) -> str:

    return await converse(
        model_id=NOVA_MICRO,
        system_prompt="""
You are a clinical information extraction assistant.

Extract only information explicitly present
in the transcript.

Do not invent clinical information.
""",
        prompt=f"""
Extract the clinically relevant information
from this transcript:

{transcript}
""",
        max_tokens=1000,
        temperature=0,
    )