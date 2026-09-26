#!/usr/bin/env python3
"""Post a generated review comment without exposing secrets or plan files."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body", type=Path, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    if not token or not repository:
        raise SystemExit("GITHUB_TOKEN and GITHUB_REPOSITORY are required")
    body = args.body.read_text(encoding="utf-8")
    if any(marker in body.lower() for marker in ("aws_secret_access_key", "private_key", "authorization: bearer")):
        raise SystemExit("refusing to post a comment containing credential markers")
    url = f"{api_url}/repos/{repository}/issues/{args.pull_request}/comments"
    request = urllib.request.Request(
        url,
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status not in (200, 201):
            raise SystemExit(f"GitHub comment failed with HTTP {response.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
