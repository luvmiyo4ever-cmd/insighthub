"""Redis-backed, one-time approvals bound to a ChatOps identity and action."""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import asdict, dataclass
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

APPROVAL_TTL_SECONDS = 60
APPROVAL_KEY_PREFIX = "chatops:approval:"
_CONSUME_IF_OWNER = """
local value = redis.call('GET', KEYS[1])
if not value then
  return false
end
local approval = cjson.decode(value)
if approval.user ~= ARGV[1] then
  return false
end
redis.call('DEL', KEYS[1])
return value
"""


class ApprovalUnavailable(RuntimeError):
    """Redis cannot safely issue or consume an approval."""


@dataclass(frozen=True)
class Approval:
    token: str
    user: str
    action: str
    arguments: dict[str, int]

    def serialize(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)

    @classmethod
    def deserialize(cls, raw: bytes | str) -> "Approval | None":
        try:
            decoded: Any = json.loads(raw)
        except (TypeError, ValueError):
            return None
        if not isinstance(decoded, dict):
            return None
        token, user, action, arguments = (
            decoded.get("token"),
            decoded.get("user"),
            decoded.get("action"),
            decoded.get("arguments"),
        )
        if (
            not all(isinstance(value, str) and value for value in (token, user, action))
            or not isinstance(arguments, dict)
            or set(arguments) != {"replicas"}
            or not isinstance(arguments["replicas"], int)
        ):
            return None
        return cls(token=token, user=user, action=action, arguments=arguments)


def _token() -> str:
    return secrets.token_urlsafe(18)


async def issue_scale_approval(*, user: str, replicas: int) -> Approval:
    approval = Approval(token=_token(), user=user, action="scale_api", arguments={"replicas": replicas})
    redis = None
    try:
        redis = await create_pool(RedisSettings.from_dsn(os.environ["REDIS_URL"]))
        stored = await redis.set(
            f"{APPROVAL_KEY_PREFIX}{approval.token}", approval.serialize(), ex=APPROVAL_TTL_SECONDS, nx=True
        )
        if not stored:
            raise ApprovalUnavailable("Could not allocate a unique approval token.")
        return approval
    except ApprovalUnavailable:
        raise
    except Exception as exc:
        raise ApprovalUnavailable("Approval storage is unavailable.") from exc
    finally:
        if redis is not None:
            await redis.aclose()


async def consume_approval(*, token: str, user: str) -> Approval | None:
    """Atomically consume only the requester's ticket; others cannot burn it."""
    redis = None
    try:
        redis = await create_pool(RedisSettings.from_dsn(os.environ["REDIS_URL"]))
        raw = await redis.eval(_CONSUME_IF_OWNER, 1, f"{APPROVAL_KEY_PREFIX}{token}", user)
    except Exception as exc:
        raise ApprovalUnavailable("Approval storage is unavailable.") from exc
    finally:
        if redis is not None:
            await redis.aclose()
    approval = Approval.deserialize(raw) if raw else None
    if approval is None or not secrets.compare_digest(approval.user, user):
        return None
    return approval
