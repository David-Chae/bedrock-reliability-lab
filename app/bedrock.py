from __future__ import annotations

import boto3
from botocore.config import Config

from .settings import settings


class BedrockService:
    def __init__(self, client=None):
        self.client = client or boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            config=Config(
                connect_timeout=5,
                read_timeout=settings.request_timeout_seconds,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )

    def ask(self, question: str) -> str:
        if not settings.model_id:
            raise RuntimeError("BEDROCK_MODEL_ID is not configured")

        response = self.client.converse(
            modelId=settings.model_id,
            system=[
                {
                    "text": (
                        "You are a concise cloud engineering assistant. "
                        "If you are uncertain, say so rather than inventing facts."
                    )
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [{"text": question}],
                }
            ],
            inferenceConfig={
                "temperature": 0.2,
                "maxTokens": 700,
            },
        )

        blocks = response["output"]["message"]["content"]
        text_parts = [b["text"] for b in blocks if "text" in b]
        return "\n".join(text_parts).strip()
