#!/usr/bin/env python3
"""Fail closed on unpinned Actions or unsafe cloud workflow boundaries."""

from __future__ import annotations

import re
from pathlib import Path


SHA = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    workflow_dir = Path(".github/workflows")
    workflows = sorted(workflow_dir.glob("*.y*ml"))
    if not workflows:
        raise SystemExit("no workflows found")
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        for use in re.findall(r"^\s*-\s*uses:\s*([^\s#]+)", text, flags=re.MULTILINE):
            if use.startswith("./"):
                continue
            if "@" not in use or not SHA.fullmatch(use.rsplit("@", 1)[1]):
                raise SystemExit(f"{path}: action is not pinned to a full SHA: {use}")
        if "@latest" in text:
            raise SystemExit(f"{path}: @latest is forbidden")

    workflow = (workflow_dir / "iac.yml").read_text(encoding="utf-8")
    if "pull_request:" not in workflow or "workflow_dispatch:" not in workflow:
        raise SystemExit("iac.yml must include PR CI and manual cloud workflow triggers")
    if workflow.count("id-token: write") != 2:
        raise SystemExit("only the plan and apply jobs may request an OIDC token")
    required_cloud_fragments = (
        "github.repository == vars.CANONICAL_REPOSITORY",
        "github.event.repository.visibility",
        "= private",
        "environment: aws-apply",
        "sha256sum -c",
        "apply -input=false",
        "source-binding.json",
        "destroy_count",
        "budget_status",
        "INFRACOST_API_KEY",
        "OPENAI_API_KEY",
    )
    for fragment in required_cloud_fragments:
        if fragment not in workflow:
            raise SystemExit(f"cloud workflow missing contract fragment: {fragment}")
    if "actions/upload-artifact" not in workflow or "actions/download-artifact" not in workflow:
        raise SystemExit("cloud workflow must use immutable plan artifacts")
    print(f"PASS: validated {len(workflows)} workflow files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
