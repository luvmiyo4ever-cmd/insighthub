"""Strict parser and policy for ChatOps permission tiers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class PermissionTier(StrEnum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


@dataclass(frozen=True)
class ScaleApiRequest:
    """The sole Day 5 write action exposed through the service catalog."""

    replicas: int

    @property
    def arguments(self) -> dict[str, int]:
        return {"replicas": self.replicas}


_MENTION = re.compile(r"<@[^>]+>")
_SCALE_API = re.compile(r"\bscale\s+(?:the\s+)?api\s+(?:to\s+)?([1-5])\b", re.IGNORECASE)
_CONFIRM = re.compile(r"^(?:confirm|approve)\s+([A-Za-z0-9_-]{16,})$", re.IGNORECASE)
_DESTRUCTIVE = re.compile(r"\b(delete|destroy|wipe|drop)\b", re.IGNORECASE)


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", _MENTION.sub(" ", text)).strip()


def parse_scale_api(text: str) -> ScaleApiRequest | None:
    match = _SCALE_API.search(normalized_text(text))
    return ScaleApiRequest(replicas=int(match.group(1))) if match else None


def parse_confirmation(text: str) -> str | None:
    match = _CONFIRM.fullmatch(normalized_text(text))
    return match.group(1) if match else None


def requests_destructive_action(text: str) -> bool:
    return bool(_DESTRUCTIVE.search(normalized_text(text)))


def confirmation_message(request: ScaleApiRequest, token: str, expires_seconds: int) -> str:
    return (
        f"Tier write: scale `insighthub-api` to {request.replicas} replicas cần xác nhận. "
        f"Gửi `confirm {token}` trong {expires_seconds} giây. "
        "Token chỉ dùng một lần và chỉ hợp lệ cho bạn cùng action này."
    )
