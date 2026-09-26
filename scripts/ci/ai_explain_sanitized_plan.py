#!/usr/bin/env python3
"""Explain only the sanitized plan summary through the OpenAI Responses API."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL")
    if not api_key or not model:
        raise SystemExit("OPENAI_API_KEY and OPENAI_MODEL are required for cloud plan explanation")

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    safe_text = json.dumps(summary, sort_keys=True)
    lowered = safe_text.lower()
    if any(marker in lowered for marker in (
        "aws_secret_access_key",
        "private_key_data",
        '"password"',
        '"secret_string"',
        '"token"',
        '"credential"',
    )):
        raise SystemExit("sanitized summary contains a forbidden sensitive field")

    payload = {
        "model": model,
        "store": False,
        "reasoning": {"effort": "low"},
        "instructions": (
            "Explain this infrastructure plan for a human reviewer. Use only the supplied sanitized counts. "
            "Call out IAM, network, data, cost, unknown values, destroy risk, and whether apply must stop. "
            "Do not invent resource values and do not request credentials."
        ),
        "input": safe_text,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        document = json.load(response)
    output_text = document.get("output_text")
    if not output_text:
        parts = []
        for item in document.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        output_text = "\n".join(parts).strip()
    if not output_text:
        raise SystemExit("Responses API returned no text output")
    args.output.write_text(output_text.rstrip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
