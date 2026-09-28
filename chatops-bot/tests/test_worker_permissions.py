"""Write actions must require a one-time, user-bound approval."""

import unittest
from unittest.mock import AsyncMock, patch

from app.approvals import Approval
from app.worker import _reply_for_event


class WorkerPermissionTests(unittest.IsolatedAsyncioTestCase):
    async def test_scale_request_only_issues_an_approval(self):
        approval = Approval("token-123456789012", "U1", "scale_api", {"replicas": 5})
        with (
            patch("app.worker.issue_scale_approval", new_callable=AsyncMock, return_value=approval) as issue,
            patch("app.worker.log_permission_decision") as audit,
            patch("app.worker.scale_api", new_callable=AsyncMock) as scale,
        ):
            reply = await _reply_for_event("<@BOT> scale api to 5", "U1")

        issue.assert_awaited_once_with(user="U1", replicas=5)
        scale.assert_not_awaited()
        audit.assert_called_once()
        self.assertIn("confirm token-123456789012", reply)

    async def test_confirmation_executes_only_the_bound_approval(self):
        approval = Approval("token-123456789012", "U1", "scale_api", {"replicas": 2})
        with (
            patch("app.worker.consume_approval", new_callable=AsyncMock, return_value=approval) as consume,
            patch("app.worker.scale_api", new_callable=AsyncMock) as scale,
            patch("app.worker.log_tool_call") as audit,
        ):
            reply = await _reply_for_event("confirm token-123456789012", "U1")

        consume.assert_awaited_once_with(token="token-123456789012", user="U1")
        scale.assert_awaited_once_with(replicas=2, approval_id="token-123456789012")
        audit.assert_called_once_with("U1", "kubernetes.deployments_scale", {"replicas": 2}, "success", approved=True)
        self.assertIn("2 replicas", reply)

    async def test_expired_or_other_user_approval_cannot_scale(self):
        with (
            patch("app.worker.consume_approval", new_callable=AsyncMock, return_value=None),
            patch("app.worker.scale_api", new_callable=AsyncMock) as scale,
            patch("app.worker.log_permission_decision") as audit,
        ):
            reply = await _reply_for_event("confirm token-123456789012", "U2")

        scale.assert_not_awaited()
        audit.assert_called_once()
        self.assertIn("Không có thay đổi", reply)

    async def test_destructive_request_is_denied(self):
        with patch("app.worker.log_permission_decision") as audit:
            reply = await _reply_for_event("<@BOT> delete api", "U1")

        audit.assert_called_once()
        self.assertIn("bị chặn", reply)
