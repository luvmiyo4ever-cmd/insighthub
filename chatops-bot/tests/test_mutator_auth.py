"""Raw-body authentication for the separately identified mutator."""

import hashlib
import hmac
import unittest

from app.mutator import MutatorAuthenticationError, verify_action_signature


class MutatorAuthenticationTests(unittest.TestCase):
    secret = "test-mutator-secret"
    timestamp = "1700000000"
    body = b'{"action":"scale_api","replicas":2,"approval_id":"token-123456789012"}'

    def signature(self) -> str:
        digest = hmac.new(
            self.secret.encode(), self.timestamp.encode("ascii") + b":" + self.body, hashlib.sha256
        ).hexdigest()
        return f"v1={digest}"

    def test_accepts_matching_current_signature(self):
        verify_action_signature(
            body=self.body,
            timestamp=self.timestamp,
            signature=self.signature(),
            secret=self.secret,
            now=float(self.timestamp),
        )

    def test_rejects_invalid_signature(self):
        with self.assertRaises(MutatorAuthenticationError):
            verify_action_signature(
                body=self.body,
                timestamp=self.timestamp,
                signature="v1=invalid",
                secret=self.secret,
                now=float(self.timestamp),
            )
