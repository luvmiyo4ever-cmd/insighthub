"""Fail-closed verification for Slack's signed HTTP Events requests."""

from __future__ import annotations

import hashlib
import hmac
import time

SLACK_SIGNATURE_VERSION = "v0"
MAX_REQUEST_AGE_SECONDS = 300


class SlackAuthenticationError(ValueError):
    """The caller did not present a valid, current Slack signature."""


class SlackConfigurationError(RuntimeError):
    """The service cannot authenticate events without an operator secret."""


def verify_slack_signature(
    *,
    body: bytes,
    timestamp: str | None,
    signature: str | None,
    signing_secret: str,
    now: float | None = None,
) -> None:
    """Verify a raw Slack request body and reject replayed or malformed requests."""
    if not signing_secret:
        raise SlackConfigurationError("SLACK_SIGNING_SECRET is not configured")
    if not timestamp or not signature:
        raise SlackAuthenticationError("Missing Slack signature headers")
    try:
        request_time = int(timestamp)
    except ValueError as exc:
        raise SlackAuthenticationError("Invalid Slack request timestamp") from exc

    current_time = time.time() if now is None else now
    if abs(current_time - request_time) > MAX_REQUEST_AGE_SECONDS:
        raise SlackAuthenticationError("Expired Slack request timestamp")

    basestring = b":".join(
        (SLACK_SIGNATURE_VERSION.encode(), timestamp.encode("ascii"), body)
    )
    expected = SLACK_SIGNATURE_VERSION + "=" + hmac.new(
        signing_secret.encode(), basestring, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise SlackAuthenticationError("Invalid Slack signature")
