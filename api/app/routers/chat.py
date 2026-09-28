"""RAG executes in FastAPI's threadpool; usage preserves its provenance."""

import time
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings
from app.core.metrics import (
    llm_call_latency,
    llm_tokens_total,
    rag_query_latency,
    record_estimated_cost,
)
from app.services.llm import generate
from app.services.retrieval import retrieve

router = APIRouter(prefix="/chat", tags=["chat"])
CHAOS_HEADER = "X-InsightHub-Chaos"
CHAOS_LLM_LATENCY = "llm-latency"
CHAOS_HTTP_ERROR = "http-error"


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class TokenUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    source: Literal["provider", "unavailable"]


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    contexts: list[dict]
    latency_ms: int
    mode: Literal["fixture", "real"]
    provider: str
    model: str
    usage: TokenUsage


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    settings = get_settings()
    chaos_scenario = request.headers.get(CHAOS_HEADER)
    if settings.day4_chaos_enabled and chaos_scenario == CHAOS_HTTP_ERROR:
        # A deliberate, scoped lab fault. It is off by default and requires both
        # operator configuration and the exact header, so normal traffic cannot
        # generate synthetic 5xx responses.
        raise HTTPException(503, "Day 4 controlled HTTP error injection")
    start = time.perf_counter()
    with rag_query_latency.time():
        contexts = retrieve(req.question, top_k=req.top_k)
        if not contexts:
            raise HTTPException(
                404, "Chưa có tài liệu nào sẵn sàng. Hãy upload tài liệu trước."
            )
        with llm_call_latency.time():
            if (
                settings.day4_chaos_enabled
                and chaos_scenario == CHAOS_LLM_LATENCY
                and settings.day4_chaos_llm_delay_seconds
            ):
                time.sleep(settings.day4_chaos_llm_delay_seconds)
            result = generate(req.question, contexts)
    for direction in ("input", "output"):
        value = result["usage"].get(f"{direction}_tokens")
        if value is not None:
            llm_tokens_total.labels(result["provider"], direction).inc(value)
            record_estimated_cost(
                result["provider"],
                f"llm_{direction}",
                value,
                getattr(settings, f"llm_{direction}_cost_usd_per_million_tokens"),
            )
    return ChatResponse(
        **result,
        contexts=contexts,
        latency_ms=int((time.perf_counter() - start) * 1000),
    )
