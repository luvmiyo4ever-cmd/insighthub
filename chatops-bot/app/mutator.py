"""Scale-only backend with its own Kubernetes ServiceAccount identity."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

MAX_REQUEST_AGE_SECONDS = 300
TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
CA_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
TARGET_NAMESPACE = "insighthub"
TARGET_DEPLOYMENT = "insighthub-api"


class MutatorAuthenticationError(ValueError):
    """The caller did not authenticate a current mutation request."""


class MutatorConfigurationError(RuntimeError):
    """The mutator lacks its independently provisioned shared secret."""


def verify_action_signature(
    *, body: bytes, timestamp: str | None, signature: str | None, secret: str, now: float | None = None
) -> None:
    if not secret:
        raise MutatorConfigurationError("Mutator signing secret is not configured.")
    if not timestamp or not signature:
        raise MutatorAuthenticationError("Missing action signature.")
    try:
        request_time = int(timestamp)
    except ValueError as exc:
        raise MutatorAuthenticationError("Invalid action timestamp.") from exc
    current_time = time.time() if now is None else now
    if abs(current_time - request_time) > MAX_REQUEST_AGE_SECONDS:
        raise MutatorAuthenticationError("Expired action timestamp.")
    expected = "v1=" + hmac.new(
        secret.encode("utf-8"), timestamp.encode("ascii") + b":" + body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise MutatorAuthenticationError("Invalid action signature.")


def _payload(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Action payload must be valid JSON.") from exc
    if (
        not isinstance(payload, dict)
        or set(payload) != {"action", "replicas", "approval_id"}
        or payload.get("action") != "scale_api"
        or not isinstance(payload.get("replicas"), int)
        or not 1 <= payload["replicas"] <= 5
        or not isinstance(payload.get("approval_id"), str)
        or len(payload["approval_id"]) < 16
    ):
        raise HTTPException(status_code=400, detail="Action is not in the scale-only service catalog.")
    return payload


async def _patch_scale(replicas: int) -> None:
    if not TOKEN_PATH.is_file() or not CA_PATH.is_file():
        raise RuntimeError("Kubernetes ServiceAccount credentials are unavailable.")
    host = os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
    port = os.environ.get("KUBERNETES_SERVICE_PORT_HTTPS", "443")
    url = f"https://{host}:{port}/apis/apps/v1/namespaces/{TARGET_NAMESPACE}/deployments/{TARGET_DEPLOYMENT}/scale"
    token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    try:
        async with httpx.AsyncClient(timeout=5.0, verify=str(CA_PATH), follow_redirects=False) as client:
            response = await client.patch(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/merge-patch+json"},
                json={"spec": {"replicas": replicas}},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError("Kubernetes rejected the scale action.") from exc


app = FastAPI(title="InsightHub approved mutator", version="0.1.0")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "insighthub-approved-mutator"}


@app.post("/v1/actions/scale-api", status_code=204)
async def scale_api(request: Request) -> None:
    body = await request.body()
    try:
        verify_action_signature(
            body=body,
            timestamp=request.headers.get("X-InsightHub-Action-Timestamp"),
            signature=request.headers.get("X-InsightHub-Action-Signature"),
            secret=os.environ.get("CHATOPS_MUTATION_SIGNING_SECRET", ""),
        )
    except MutatorConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Mutator authentication is not configured.") from exc
    except MutatorAuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Invalid mutator authentication.") from exc
    payload = _payload(body)
    try:
        await _patch_scale(payload["replicas"])
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail="Scale action was not accepted by Kubernetes.") from exc
