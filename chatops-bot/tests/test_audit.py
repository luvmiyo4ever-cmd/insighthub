"""Audit records must remain structured and avoid operation output."""

import json
import os
import unittest
from pathlib import Path

from app.audit import log_tool_call


class AuditTests(unittest.TestCase):
    def test_tool_call_is_structured(self):
        with self.assertLogs("chatops-bot.audit", level="INFO") as captured:
            log_tool_call("U123", "kubernetes.pods_list_in_namespace", {"namespace": "insighthub"}, "success")

        record = json.loads(captured.output[0].split(":", 2)[-1])
        self.assertEqual(record["user"], "U123")
        self.assertEqual(record["tool"], "kubernetes.pods_list_in_namespace")
        self.assertEqual(record["args"], {"namespace": "insighthub"})
        self.assertEqual(record["result"], "success")
        self.assertTrue(record["approved"])
        self.assertIn("ts", record)

    def test_tool_call_is_appended_to_audit_file(self):
        audit_path = Path(os.environ.get("CHATOPS_AUDIT_LOG_PATH", "/app/audit/chatops-audit.log"))
        log_tool_call("U456", "prometheus.query", {"query_id": "insighthub_up"}, "success")

        record = json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(record["user"], "U456")
        self.assertEqual(record["tool"], "prometheus.query")
