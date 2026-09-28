"""Slack event projection and deduplication identity tests."""

import unittest

from app.queue import SlackEventError, build_job


class SlackEventProjectionTests(unittest.TestCase):
    payload = {
        "type": "event_callback",
        "event_id": "Ev-1",
        "event": {
            "type": "app_mention",
            "channel": "C1",
            "user": "U1",
            "text": "<@BOT> api healthy?",
            "ts": "123.456",
        },
    }

    def test_projects_only_fields_needed_by_the_worker(self):
        self.assertEqual(
            build_job(self.payload),
            {
                "event_id": "Ev-1",
                "channel": "C1",
                "user": "U1",
                "text": "<@BOT> api healthy?",
                "thread_ts": "123.456",
            },
        )

    def test_ignores_bot_events_to_prevent_reply_loops(self):
        payload = {**self.payload, "event": {**self.payload["event"], "bot_id": "B1"}}
        self.assertIsNone(build_job(payload))

    def test_rejects_incomplete_app_mention(self):
        payload = {**self.payload, "event_id": ""}
        with self.assertRaises(SlackEventError):
            build_job(payload)
