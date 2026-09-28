"""Deterministic routing for the three Day 5 read-only Slack intents."""

from enum import StrEnum
import re


class Intent(StrEnum):
    API_HEALTH = "api_health"
    INGESTION_TODAY = "ingestion_today"
    FAILING_PODS = "failing_pods"


def classify_question(question: str) -> Intent | None:
    """Classify a Slack mention without treating its text as an instruction.

    The matching vocabulary is intentionally small and auditable. New tool
    capabilities must be added explicitly rather than inferred by an LLM.
    """
    normalized = re.sub(r"<@[^>]+>", " ", question.casefold())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if any(phrase in normalized for phrase in (
        "api healthy", "api health", "insighthub có healthy", "insighthub co healthy",
        "api có khỏe", "api co khoe", "api có khoẻ", "api co khoẻ",
    )):
        return Intent.API_HEALTH
    if any(phrase in normalized for phrase in (
        "ingest count today", "ingest bao nhiêu", "ingest bao nhieu",
        "hôm nay ingest", "hom nay ingest", "bao nhiêu doc hôm nay",
        "bao nhieu doc hom nay", "documents today",
    )):
        return Intent.INGESTION_TODAY
    if any(phrase in normalized for phrase in (
        "which pods failing", "pod nào đang lỗi", "pod nao dang loi",
        "pod nào lỗi", "pod nao loi", "failing pods",
    )):
        return Intent.FAILING_PODS
    return None


def help_message() -> str:
    return (
        "Mình hỗ trợ ba câu hỏi read-only: `api healthy?`, "
        "`ingest count today?`, hoặc `which pods failing?`"
    )
