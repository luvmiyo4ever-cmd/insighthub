#!/usr/bin/env python3
"""Create a non-sensitive Terraform plan summary for review and PR comments."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


SENSITIVE_MARKERS = (
    "password",
    "secret",
    "token",
    "credential",
    "private_key",
    "access_key",
)


def count_unknown(value: Any) -> int:
    if value is True:
        return 1
    if isinstance(value, dict):
        return sum(count_unknown(child) for child in value.values())
    if isinstance(value, list):
        return sum(count_unknown(child) for child in value)
    return 0


def risk_bucket(address: str, resource_type: str) -> str | None:
    text = f"{address} {resource_type}".lower()
    if any(marker in text for marker in ("iam", "oidc", "role", "policy")):
        return "IAM"
    if any(marker in text for marker in ("vpc", "subnet", "security_group", "route", "nat", "eks", "load_balancer")):
        return "network"
    if any(marker in text for marker in ("rds", "db_instance", "elasticache", "redis", "s3", "kms", "secretsmanager", "secret")):
        return "data"
    return None


def load_cost(path: Path | None) -> tuple[float | None, str]:
    if path is None or not path.exists():
        return None, "unknown"
    document = json.loads(path.read_text(encoding="utf-8"))
    candidates: list[float] = []
    if isinstance(document.get("totalMonthlyCost"), str):
        candidates.append(float(document["totalMonthlyCost"]))
    for project in document.get("projects", []):
        value = project.get("breakdown", {}).get("totalMonthlyCost")
        if isinstance(value, str):
            candidates.append(float(value))
    if not candidates:
        return None, "unknown"
    return sum(candidates), "known"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--summary-md", type=Path, required=True)
    parser.add_argument("--cost-json", type=Path)
    parser.add_argument("--budget-usd", type=float)
    args = parser.parse_args()

    plan = json.loads(args.plan_json.read_text(encoding="utf-8"))
    counts = {"create": 0, "update": 0, "delete": 0, "read": 0, "replace": 0}
    resources: list[dict[str, str]] = []
    risks = {"IAM": 0, "network": 0, "data": 0}
    unknown_values = 0

    for item in plan.get("resource_changes", []):
        change = item.get("change", {})
        actions = change.get("actions", [])
        address = str(item.get("address", "unknown"))
        resource_type = str(item.get("type", "unknown"))
        for action in actions:
            counts[action] = counts.get(action, 0) + 1
        if actions == ["delete", "create"] or actions == ["create", "delete"]:
            counts["replace"] += 1
        material_change = any(action in actions for action in ("create", "update", "delete"))
        bucket = risk_bucket(address, resource_type) if material_change else None
        if bucket:
            risks[bucket] += 1
        unknown_values += count_unknown(change.get("after_unknown", {}))
        resources.append({"address": address, "type": resource_type, "actions": ",".join(actions)})

    estimated_cost, cost_status = load_cost(args.cost_json)
    if args.budget_usd is None or estimated_cost is None:
        budget_status = "unknown"
    elif estimated_cost <= args.budget_usd:
        budget_status = "within"
    else:
        budget_status = "exceeded"

    summary = {
        "source_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "repository": os.environ.get("GITHUB_REPOSITORY", "unknown"),
        "create_count": counts.get("create", 0),
        "change_count": counts.get("update", 0),
        "destroy_count": counts.get("delete", 0) + counts.get("replace", 0),
        "replace_count": counts.get("replace", 0),
        "read_count": counts.get("read", 0),
        "unknown_value_count": unknown_values,
        "risk_counts": risks,
        "estimated_monthly_usd": estimated_cost,
        "cost_status": cost_status,
        "budget_usd": args.budget_usd,
        "budget_status": budget_status,
        "human_review_required": True,
        "resources": resources,
    }
    args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    cost_line = "unknown"
    if estimated_cost is not None:
        cost_line = f"${estimated_cost:.2f}/month"
    budget_line = budget_status if args.budget_usd is not None else "unknown (budget input missing)"
    risk_line = ", ".join(f"{name}={count}" for name, count in risks.items())
    conclusion = "HUMAN REVIEW REQUIRED"
    if summary["destroy_count"] > 0:
        conclusion = "BLOCKED: unexpected destroy/replacement"
    elif budget_status == "exceeded":
        conclusion = "BLOCKED: estimated cost exceeds budget"
    elif args.budget_usd is None:
        conclusion = "BLOCKED: budget input missing"

    markdown = f"""## Terraform plan review (sanitized)

Source: `{summary['repository']}@{summary['source_sha']}`

| create | change | destroy/replacement | unknown values |
|---:|---:|---:|---:|
| {summary['create_count']} | {summary['change_count']} | {summary['destroy_count']} | {summary['unknown_value_count']} |

- IAM risk: `{risks['IAM']}` changed resources
- Network risk: `{risks['network']}` changed resources
- Data risk: `{risks['data']}` changed resources
- Estimated cost: `{cost_line}`; budget status: `{budget_line}`
- Unknown values are counted but their values are intentionally omitted.
- Raw plan, state, credentials, and sensitive attributes are not included here.

**Conclusion: {conclusion}.** Apply requires a protected Environment approval,
the exact saved plan checksum, and a source-binding match.
"""
    args.summary_md.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
