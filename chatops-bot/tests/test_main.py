"""Endpoint tests that do not require a Slack workspace or network transport."""

import asyncio
import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.main import slack_events


class RawRequest:
    def __init__(self, body: bytes, headers: dict[str, str]):
        self._body = body
        self.headers = headers

    async def body(self) -> bytes:
        return self._body


class SlackEventsEndpointTests(unittest.TestCase):
    secret = "test-signing-secret"
    timestamp = "1700000000"

    def signed_request(self, payload: dict) -> RawRequest:
        body = json.dumps(payload, separators=(",", ":")).encode()
        base = b"v0:" + self.timestamp.encode("ascii") + b":" + body
        signature = "v0=" + hmac.new(
            self.secret.encode(), base, hashlib.sha256
        ).hexdigest()
        return RawRequest(
            body,
            {
                "X-Slack-Request-Timestamp": self.timestamp,
                "X-Slack-Signature": signature,
            },
        )

    def test_url_verification_returns_challenge_after_signature_check(self):
        request = self.signed_request({"type": "url_verification", "challenge": "verify-me"})
        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": self.secret}, clear=False), patch(
            "app.slack_auth.time.time", return_value=float(self.timestamp)
        ):
            result = asyncio.run(slack_events(request))
        self.assertEqual(result, {"challenge": "verify-me"})

    def test_invalid_signature_is_rejected_before_payload_handling(self):
        request = RawRequest(
            b'{"type":"url_verification","challenge":"verify-me"}',
            {
                "X-Slack-Request-Timestamp": self.timestamp,
                "X-Slack-Signature": "v0=invalid",
            },
        )
        with patch.dict(os.environ, {"SLACK_SIGNING_SECRET": self.secret}, clear=False), patch(
            "app.slack_auth.time.time", return_value=float(self.timestamp)
        ), self.assertRaises(HTTPException) as raised:
            asyncio.run(slack_events(request))
        self.assertEqual(raised.exception.status_code, 401)

    def test_app_mention_is_acknowledged_after_durable_enqueue(self):
        payload = {
            "type": "event_callback",
            "event_id": "Ev-123",
            "event": {
                "type": "app_mention",
                "channel": "C1",
                "user": "U1",
                "text": "<@B1> api healthy?",
                "ts": "123.45",
            },
        }
        request = self.signed_request(payload)
        with patch.dict(
            os.environ,
            {"SLACK_SIGNING_SECRET": self.secret, "SLACK_BOT_TOKEN": "xoxb-test"},
            clear=False,
        ), patch("app.slack_auth.time.time", return_value=float(self.timestamp)), patch(
            "app.main.enqueue_event", return_value=True
        ) as enqueue:
            result = asyncio.run(slack_events(request))
        self.assertEqual(result, {"ok": "true"})
        self.assertEqual(enqueue.call_args.args[0]["event_id"], "Ev-123")
