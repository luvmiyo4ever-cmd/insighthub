"""Unit tests for raw-body Slack request authentication."""

import hashlib
import hmac
import unittest

from app.slack_auth import (
    MAX_REQUEST_AGE_SECONDS,
    SlackAuthenticationError,
    SlackConfigurationError,
    verify_slack_signature,
)


class SlackSignatureTests(unittest.TestCase):
    secret = "test-signing-secret"
    timestamp = "1700000000"
    body = b'{"type":"event_callback"}'

    def signature(self) -> str:
        base = b"v0:" + self.timestamp.encode("ascii") + b":" + self.body
        digest = hmac.new(self.secret.encode(), base, hashlib.sha256).hexdigest()
        return "v0=" + digest

    def test_accepts_current_raw_body_with_matching_signature(self):
        verify_slack_signature(
            body=self.body,
            timestamp=self.timestamp,
            signature=self.signature(),
            signing_secret=self.secret,
            now=float(self.timestamp),
        )

    def test_rejects_invalid_signature(self):
        with self.assertRaises(SlackAuthenticationError):
            verify_slack_signature(
                body=self.body,
                timestamp=self.timestamp,
                signature="v0=not-a-valid-signature",
                signing_secret=self.secret,
                now=float(self.timestamp),
            )

    def test_rejects_stale_timestamp(self):
        with self.assertRaises(SlackAuthenticationError):
            verify_slack_signature(
                body=self.body,
                timestamp=self.timestamp,
                signature=self.signature(),
                signing_secret=self.secret,
                now=float(self.timestamp) + MAX_REQUEST_AGE_SECONDS + 1,
            )

    def test_rejects_missing_secret(self):
        with self.assertRaises(SlackConfigurationError):
            verify_slack_signature(
                body=self.body,
                timestamp=self.timestamp,
                signature=self.signature(),
                signing_secret="",
                now=float(self.timestamp),
            )
