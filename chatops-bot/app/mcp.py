"""Small, bounded Streamable HTTP MCP client for the Day 2 backends."""

import json
import os
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

import httpx

MCP_PROTOCOL_VERSION = "2025-11-25"
MAX_MCP_RESPONSE_BYTES = 64 * 1024
# Slack is ACKed before this worker call. Keep a finite MCP deadline while
# allowing Kubernetes API discovery in a freshly started local cluster.
MCP_TIMEOUT_SECONDS = 15.0


class McpError(RuntimeError):
    """A configured MCP backend rejected or could not serve a read-only call."""


def _endpoint(environment_name: str) -> str:
    raw = os.environ.get(environment_name, "")
    parsed = urlsplit(raw)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"host.docker.internal", "127.0.0.1", "localhost"}
        or parsed.username
        or parsed.password
        or parsed.path != "/mcp"
        or parsed.query
        or parsed.fragment
    ):
        raise McpError(f"{environment_name} is not configured.")
    return parsed.geturl()


async def call_tool(backend: str, name: str, arguments: Mapping[str, Any]) -> str:
    """Call one fixed tool and return only bounded text content.

    The caller owns the tool and argument allowlists; Slack text is never used
    for a URL, tool name, or argument.
    """
    environment_name = {
        "kubernetes": "MCP_KUBERNETES_URL",
        "prometheus": "MCP_PROMETHEUS_URL",
    }.get(backend)
    if environment_name is None:
        raise McpError("Unsupported MCP backend.")
    endpoint = _endpoint(environment_name)
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        # The local kubectl port-forward listens only on host loopback. Docker
        # reaches it through host.docker.internal, while both Day 2 MCP servers
        # correctly reject that external Host header as DNS-rebinding defense.
        # Preserve localhost as the logical host; the endpoint itself remains
        # constrained to the local bridge allowlist above.
        "Host": "localhost",
    }
    try:
        async with httpx.AsyncClient(timeout=MCP_TIMEOUT_SECONDS, follow_redirects=False) as client:
            initialized = await client.post(
                endpoint,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "initialize",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": MCP_PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "insighthub-chatops", "version": "0.2.0"},
                    },
                },
            )
            session_id = initialized.headers.get("Mcp-Session-Id")
            _result(initialized)
            request_headers = {**headers, **({"Mcp-Session-Id": session_id} if session_id else {})}
            ready = await client.post(
                endpoint,
                headers=request_headers,
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            )
            if ready.status_code not in {200, 202, 204}:
                _result(ready)
            response = await client.post(
                endpoint,
                headers=request_headers,
                json={
                    "jsonrpc": "2.0",
                    "id": "tool-call",
                    "method": "tools/call",
                    "params": {"name": name, "arguments": dict(arguments)},
                },
            )
    except httpx.HTTPError as exc:
        raise McpError(f"{backend} MCP backend is unavailable.") from exc
    result = _result(response)
    content = result.get("content") if isinstance(result, dict) else None
    if not isinstance(content, list):
        raise McpError(f"{backend} MCP response is invalid.")
    text = "\n".join(
        item["text"] for item in content
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str)
    )
    if not text:
        raise McpError(f"{backend} MCP response has no text result.")
    return text[:MAX_MCP_RESPONSE_BYTES]


def _result(response: httpx.Response) -> dict[str, Any]:
    if response.status_code != 200:
        raise McpError("MCP backend returned an unexpected HTTP status.")
    content_length = response.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_MCP_RESPONSE_BYTES:
        raise McpError("MCP response exceeds the configured size limit.")
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
    try:
        if content_type == "application/json":
            payload = response.json()
        elif content_type == "text/event-stream":
            payload = _sse_payload(response.text)
        else:
            raise McpError("MCP backend returned an unsupported content type.")
    except ValueError as exc:
        raise McpError("MCP backend did not return valid JSON.") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("result"), dict) or payload.get("error"):
        raise McpError("MCP tool call was rejected.")
    return payload["result"]


def _sse_payload(body: str) -> dict[str, Any]:
    """Read the first JSON-RPC result event; event framing is never reflected."""
    if len(body.encode("utf-8")) > MAX_MCP_RESPONSE_BYTES:
        raise McpError("MCP response exceeds the configured size limit.")
    for line in body.splitlines():
        if not line.startswith("data: "):
            continue
        payload = json.loads(line[6:])
        if isinstance(payload, dict) and ("result" in payload or "error" in payload):
            return payload
    raise McpError("MCP response did not contain a JSON-RPC result.")
