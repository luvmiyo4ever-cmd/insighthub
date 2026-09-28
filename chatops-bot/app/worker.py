"""ARQ worker that answers verified Slack app mentions after the HTTP ACK."""

import os

from arq.connections import RedisSettings

from app.approvals import APPROVAL_TTL_SECONDS, ApprovalUnavailable, consume_approval, issue_scale_approval
from app.audit import log_permission_decision, log_tool_call
from app.intents import classify_question, help_message
from app.mutation_client import MutationUnavailable, scale_api
from app.operations import OperationsError, answer
from app.permissions import (
    PermissionTier,
    confirmation_message,
    parse_confirmation,
    parse_scale_api,
    requests_destructive_action,
)
from app.queue import CHATOPS_QUEUE_NAME
from app.slack_client import post_thread_reply


async def process_slack_event(_ctx, event: dict[str, str]) -> None:
    reply = await _reply_for_event(event["text"], event["user"])
    await post_thread_reply(
        channel=event["channel"],
        thread_ts=event["thread_ts"],
        text=reply,
    )


async def _reply_for_event(text: str, user: str) -> str:
    """Enforce read/write/destructive policy before any backend operation."""
    scale_request = parse_scale_api(text)
    if scale_request is not None:
        try:
            approval = await issue_scale_approval(user=user, replicas=scale_request.replicas)
        except ApprovalUnavailable:
            log_permission_decision(
                user, PermissionTier.WRITE, "scale_api", scale_request.arguments, "approval_unavailable", False
            )
            return "Không thể tạo approval cho scale action lúc này. Không có thay đổi nào được thực hiện."
        log_permission_decision(user, PermissionTier.WRITE, approval.action, approval.arguments, "pending", False)
        return confirmation_message(scale_request, approval.token, APPROVAL_TTL_SECONDS)

    token = parse_confirmation(text)
    if token is not None:
        try:
            approval = await consume_approval(token=token, user=user)
        except ApprovalUnavailable:
            log_permission_decision(user, PermissionTier.WRITE, "scale_api", {}, "approval_unavailable", False)
            return "Không thể kiểm tra approval lúc này. Không có thay đổi nào được thực hiện."
        if approval is None:
            log_permission_decision(user, PermissionTier.WRITE, "scale_api", {}, "rejected_or_expired", False)
            return "Approval không hợp lệ, đã hết hạn, đã dùng, hoặc không thuộc về bạn. Không có thay đổi nào được thực hiện."
        try:
            await scale_api(replicas=approval.arguments["replicas"], approval_id=approval.token)
        except MutationUnavailable:
            log_tool_call(user, "kubernetes.deployments_scale", approval.arguments, "failure", approved=True)
            return "Scale action đã được approve nhưng mutator không thực hiện được. Kiểm tra audit và backend; không retry token này."
        log_tool_call(user, "kubernetes.deployments_scale", approval.arguments, "success", approved=True)
        return f"Đã scale `insighthub-api` lên {approval.arguments['replicas']} replicas theo approval của bạn."

    if requests_destructive_action(text):
        log_permission_decision(user, PermissionTier.DESTRUCTIVE, "unavailable", {}, "denied", False)
        return "Tier destructive bị chặn: ChatOps không có destructive action trong service catalog. Dùng quy trình break-glass ngoài Slack."

    intent = classify_question(text)
    if intent is None:
        return help_message()
    try:
        return await answer(intent, user=user)
    except OperationsError as exc:
        return str(exc)


class WorkerSettings:
    functions = [process_slack_event]
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://redis:6379/1"))
    queue_name = CHATOPS_QUEUE_NAME
    max_tries = 3
    job_timeout = 30
