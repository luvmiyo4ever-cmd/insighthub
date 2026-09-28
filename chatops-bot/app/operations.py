"""Bounded read-only data operations behind the three ChatOps intents."""

import os
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from app.audit import log_tool_call
from app.intents import Intent
from app.mcp import McpError, call_tool

HTTP_TIMEOUT_SECONDS = 3.0


class OperationsError(RuntimeError):
    """An operator-configured read-only backend did not return safe data."""


def _validated_origin(raw: str, allowed_hosts: set[str], schemes: set[str]) -> str:
    parsed = urlsplit(raw)
    if (
        parsed.scheme not in schemes
        or parsed.hostname not in allowed_hosts
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise OperationsError("The read-only backend URL is invalid.")
    return parsed.geturl().rstrip("/")


async def answer(intent: Intent, *, user: str, now: datetime | None = None) -> str:
    if intent is Intent.API_HEALTH:
        return await _api_health(user=user)
    if intent is Intent.INGESTION_TODAY:
        return await _ingestion_today(user=user, now=now or datetime.now(timezone.utc))
    if intent is Intent.FAILING_PODS:
        return await _failing_pods(user=user)
    raise OperationsError("Unsupported intent.")


async def _api_health(*, user: str) -> str:
    try:
        prometheus = await call_tool(
            "prometheus", "query", {"query": 'up{job=~"insighthub-api|insighthub-worker"}'}
        )
        log_tool_call(user, "prometheus.query", {"query_id": "insighthub_up"}, "success")
    except McpError as exc:
        log_tool_call(user, "prometheus.query", {"query_id": "insighthub_up"}, "failure")
        raise OperationsError("Prometheus MCP backend is unavailable.") from exc
    if "=> 0" in prometheus:
        return "InsightHub có target Prometheus đang down; kiểm tra dashboard hoặc pod lỗi."
    return "InsightHub API healthy theo Prometheus MCP."


def _api_origin() -> str:
    # Temporary compatibility for the ingestion-count intent; it does not receive
    # Slack-controlled input. Health and pod status use the Day 2 MCP backends.
    return _validated_origin(os.environ.get("INSIGHTHUB_API_URL", "http://api:8000"), {"api", "127.0.0.1", "localhost"}, {"http"})


async def _ingestion_today(*, user: str, now: datetime) -> str:
    origin = _api_origin()
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=False) as client:
            response = await client.get(f"{origin}/documents")
            response.raise_for_status()
            documents = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        log_tool_call(user, "insighthub.documents_list", {}, "failure")
        raise OperationsError("Không thể đọc trạng thái ingestion từ InsightHub API.") from exc
    if not isinstance(documents, list):
        log_tool_call(user, "insighthub.documents_list", {}, "failure")
        raise OperationsError("InsightHub documents response is invalid.")
    log_tool_call(user, "insighthub.documents_list", {}, "success")

    statuses = {"pending": 0, "processing": 0, "ready": 0, "failed": 0}
    for document in documents:
        if not isinstance(document, dict) or not isinstance(document.get("created_at"), str):
            continue
        try:
            created_at = datetime.fromisoformat(document["created_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if created_at.astimezone(timezone.utc).date() != now.astimezone(timezone.utc).date():
            continue
        status = document.get("status")
        if status in statuses:
            statuses[status] += 1
    total = sum(statuses.values())
    return (
        f"Hôm nay có {total} document được upload: "
        f"{statuses['ready']} ready, {statuses['pending']} pending, "
        f"{statuses['processing']} processing, {statuses['failed']} failed."
    )


async def _failing_pods(*, user: str) -> str:
    try:
        pods = await call_tool("kubernetes", "pods_list_in_namespace", {"namespace": "insighthub"})
        log_tool_call(user, "kubernetes.pods_list_in_namespace", {"namespace": "insighthub"}, "success")
    except McpError as exc:
        log_tool_call(user, "kubernetes.pods_list_in_namespace", {"namespace": "insighthub"}, "failure")
        raise OperationsError("Kubernetes MCP backend is unavailable.") from exc
    failing = _failing_pod_summaries(pods)
    if not failing:
        return "Kubernetes MCP không báo pod lỗi trong namespace `insighthub`."
    return "Pod cần chú ý theo Kubernetes MCP:\n" + "\n".join(failing[:10])


def _failing_pod_summaries(pods: str) -> list[str]:
    """Project the MCP table into the only safe Slack-facing pod fields."""
    summaries: list[str] = []
    for line in pods.splitlines():
        fields = line.split()
        # `pods_list_in_namespace` table format begins with namespace, API
        # version, kind, name, ready, and status. Ignore malformed rows rather
        # than reflect labels or arbitrary server output to Slack.
        if len(fields) < 6 or fields[0] != "insighthub":
            continue
        name, ready, status = fields[3], fields[4], fields[5]
        searchable = f"{ready} {status}".lower()
        if status.lower() == "completed" or not any(
            marker in searchable for marker in ("failed", "unknown", "crashloop", "error", "0/")
        ):
            continue
        summaries.append(f"- `{name}`: {status} ({ready} Ready)")
    return summaries
