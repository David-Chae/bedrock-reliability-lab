import os


class Settings:
    aws_region: str = os.getenv("AWS_REGION", "ap-southeast-2")
    model_id: str = os.getenv("BEDROCK_MODEL_ID", "")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


settings = Settings()
