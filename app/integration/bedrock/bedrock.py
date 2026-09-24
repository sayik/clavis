import aioboto3
from botocore.config import Config


AWS_REGION = "us-east-1"

session = aioboto3.Session()


async def converse(
    model_id: str,
    prompt: str,
    *,
    system_prompt: str | None = None,
    max_tokens: int = 1000,
    temperature: float = 0.0,
) -> str:

    async with session.client(
        "bedrock-runtime",
        region_name=AWS_REGION,
        config=Config(
            read_timeout=3600,
            connect_timeout=10,
            retries={"max_attempts": 3},
        ),
    ) as bedrock:

        request = {
            "modelId": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": prompt}
                    ],
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        }

        if system_prompt:
            request["system"] = [
                {"text": system_prompt}
            ]

        response = await bedrock.converse(**request)

        return response["output"]["message"]["content"][0]["text"]