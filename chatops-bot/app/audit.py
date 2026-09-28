"""Structured audit output for every bounded ChatOps tool call."""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG_PATH = Path(os.environ.get("CHATOPS_AUDIT_LOG_PATH", "/app/audit/chatops-audit.log"))


def _configure_logger() -> logging.Logger:
    """Send one compact JSON line to stdout and the persistent audit file."""
    logger = logging.getLogger("chatops-bot.audit")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formatter = logging.Formatter("%(message)s")
    stdout = logging.StreamHandler()
    stdout.setFormatter(formatter)
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(AUDIT_LOG_PATH, encoding="utf-8")
    except OSError as exc:
        raise RuntimeError("ChatOps audit log file is not writable.") from exc
    file_handler.setFormatter(formatter)
    logger.addHandler(stdout)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


logger = _configure_logger()


def _write_record(record: dict) -> None:
    logger.info(json.dumps(record, ensure_ascii=False, separators=(",", ":")))


def log_tool_call(
    user: str,
    tool: str,
    args: dict,
    result_summary: str,
    approved: bool = True,
) -> None:
    """Write one JSON record without logging secrets, content, or tool output."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "tool": tool,
        "args": args,
        "result": result_summary,
        "approved": approved,
    }
    _write_record(record)


def log_permission_decision(
    user: str, tier: str, action: str, args: dict, result_summary: str, approved: bool
) -> None:
    """Record a decision without storing a confirmation token or Slack text."""
    _write_record(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "tier": tier,
            "action": action,
            "args": args,
            "result": result_summary,
            "approved": approved,
        }
    )
