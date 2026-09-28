"""Authenticated client for the separately identified scale-only backend."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlsplit

import httpx

MUTATOR_TIMEOUT_SECONDS = 5.0


class MutationUnavailable(RuntimeError):
    """The approved mutator could not safely perform its single action."""


def _endpoint() -> str:
    raw = os.environ.get("CHATOPS_MUTATOR_URL", "")
    parsed = urlsplit(raw)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"host.docker.internal", "127.0.0.1", "localhost"}
        or parsed.username
        or parsed.password
        or parsed.path != "/v1/actions/scale-api"
        or parsed.query
        or parsed.fragment
    ):
        raise MutationUnavailable("The approved mutator URL is not configured.")
    return parsed.geturl()


async def scale_api(*, replicas: int, approval_id: str) -> None:
    """Submit only an already-approved scale request to the local mutator."""
    secret = os.environ.get("CHATOPS_MUTATION_SIGNING_SECRET", "")
    if not secret:
        raise MutationUnavailable("The approved mutator identity is not configured.")
    payload = json.dumps(
        {"action": "scale_api", "replicas": replicas, "approval_id": approval_id},
        separators=(",", ":"),
    ).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode("utf-8"), timestamp.encode("ascii") + b":" + payload, hashlib.sha256).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=MUTATOR_TIMEOUT_SECONDS, follow_redirects=False) as client:
            response = await client.post(
                _endpoint(),
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-InsightHub-Action-Timestamp": timestamp,
                    "X-InsightHub-Action-Signature": f"v1={signature}",
                    "Host": "localhost",
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise MutationUnavailable("The approved mutator is unavailable or rejected the action.") from exc
