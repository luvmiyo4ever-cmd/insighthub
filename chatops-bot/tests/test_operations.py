"""Tests for the fixed, read-only MCP operations behind ChatOps intents."""

import unittest
from unittest.mock import AsyncMock, patch

from app.intents import Intent
from app.mcp import McpError
from app.operations import OperationsError, answer


class OperationsTests(unittest.IsolatedAsyncioTestCase):
    async def test_failing_pods_uses_namespaced_kubernetes_tool(self):
        response = """NAMESPACE APIVERSION KIND NAME READY STATUS
insighthub v1 Pod api 0/1 Unknown
insighthub v1 Pod migration 0/1 Completed
"""
        with (
            patch("app.operations.call_tool", new_callable=AsyncMock, return_value=response) as call_tool,
            patch("app.operations.log_tool_call") as audit,
        ):
            result = await answer(Intent.FAILING_PODS, user="U123")

        call_tool.assert_awaited_once_with(
            "kubernetes", "pods_list_in_namespace", {"namespace": "insighthub"}
        )
        audit.assert_called_once_with(
            "U123", "kubernetes.pods_list_in_namespace", {"namespace": "insighthub"}, "success"
        )
        self.assertIn("- `api`: Unknown (0/1 Ready)", result)
        self.assertNotIn("Completed", result)

    async def test_health_uses_fixed_prometheus_query(self):
        with (
            patch("app.operations.call_tool", new_callable=AsyncMock, return_value="up => 1") as call_tool,
            patch("app.operations.log_tool_call") as audit,
        ):
            result = await answer(Intent.API_HEALTH, user="U123")

        call_tool.assert_awaited_once_with(
            "prometheus", "query", {"query": 'up{job=~"insighthub-api|insighthub-worker"}'}
        )
        audit.assert_called_once_with("U123", "prometheus.query", {"query_id": "insighthub_up"}, "success")
        self.assertIn("healthy", result)

    async def test_health_audits_an_unavailable_mcp_backend(self):
        with (
            patch("app.operations.call_tool", new_callable=AsyncMock, side_effect=McpError("unavailable")),
            patch("app.operations.log_tool_call") as audit,
        ):
            with self.assertRaisesRegex(OperationsError, "Prometheus MCP backend is unavailable"):
                await answer(Intent.API_HEALTH, user="U123")

        audit.assert_called_once_with("U123", "prometheus.query", {"query_id": "insighthub_up"}, "failure")
