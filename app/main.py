from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .bedrock import BedrockService
from .settings import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("bedrock-reliability-lab")

app = FastAPI(title="Bedrock Reliability Lab", version="0.1.0")
bedrock = BedrockService()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)


class AskResponse(BaseModel):
    answer: str
    request_id: str
    latency_ms: int
    model_id: str


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": locals().get("status_code", 500),
                    "latency_ms": latency_ms,
                }
            )
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not settings.model_id:
        raise HTTPException(status_code=503, detail="BEDROCK_MODEL_ID is not configured")
    return {"status": "ready", "region": settings.aws_region}


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, request: Request):
    request_id = request.state.request_id
    started = time.perf_counter()

    try:
        answer = bedrock.ask(payload.question)
    except Exception as exc:
        logger.exception(
            json.dumps(
                {
                    "event": "bedrock_failure",
                    "request_id": request_id,
                    "error_type": type(exc).__name__,
                }
            )
        )
        raise HTTPException(status_code=502, detail="Bedrock invocation failed") from exc

    latency_ms = int((time.perf_counter() - started) * 1000)

    logger.info(
        json.dumps(
            {
                "event": "bedrock_success",
                "request_id": request_id,
                "model_id": settings.model_id,
                "latency_ms": latency_ms,
            }
        )
    )

    return AskResponse(
        answer=answer,
        request_id=request_id,
        latency_ms=latency_ms,
        model_id=settings.model_id,
    )
