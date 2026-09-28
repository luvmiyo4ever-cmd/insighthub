"""Permission tiers and confirmation command parsing stay narrow."""

import unittest

from app.permissions import (
    ScaleApiRequest,
    parse_confirmation,
    parse_scale_api,
    requests_destructive_action,
)


class PermissionParserTests(unittest.TestCase):
    def test_scale_api_is_bounded_to_the_service_catalog(self):
        self.assertEqual(parse_scale_api("<@BOT> scale api to 5"), ScaleApiRequest(replicas=5))
        self.assertIsNone(parse_scale_api("scale worker to 5"))
        self.assertIsNone(parse_scale_api("scale api to 6"))

    def test_confirmation_requires_only_a_token(self):
        self.assertEqual(parse_confirmation("confirm safe_token-123456789"), "safe_token-123456789")
        self.assertIsNone(parse_confirmation("confirm safe_token-123456789 and delete postgres"))

    def test_destructive_words_are_blocked_before_intent_routing(self):
        self.assertTrue(requests_destructive_action("delete the api"))
        self.assertFalse(requests_destructive_action("scale api to 2"))
