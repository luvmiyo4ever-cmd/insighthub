#!/usr/bin/env python3
"""Exact local-kind smoke: health, 202 upload, Ready <=30s, chat citations."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


API = os.environ.get("API_URL", "http://127.0.0.1:8000")
WEB = os.environ.get("WEB_URL", "http://127.0.0.1:3000")


def request(url: str, method: str = "GET", body: bytes | None = None, headers=None):
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def main() -> int:
    for url in (f"{API}/healthz", f"{API}/readyz", f"{WEB}/api/health"):
        status, _ = request(url)
        assert status == 200, (url, status)

    boundary = "kind-" + uuid.uuid4().hex
    filename = "kind-smoke-" + uuid.uuid4().hex + ".md"
    sample = Path(__file__).resolve().parents[1] / "sample-docs" / "so-tay-van-hanh.md"
    content = sample.read_bytes()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        "Content-Type: text/markdown\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    started = time.monotonic()
    status, raw = request(
        f"{API}/documents",
        "POST",
        body,
        {"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    assert status == 202, status
    document_id = json.loads(raw)["id"]

    deadline = started + 30
    document = None
    while time.monotonic() < deadline:
        status, raw = request(f"{API}/documents")
        assert status == 200, status
        rows = json.loads(raw)
        matches = [row for row in rows if str(row.get("id")) == str(document_id)]
        if matches and matches[0]["status"] == "ready":
            document = matches[0]
            break
        if matches and matches[0]["status"] == "failed":
            raise AssertionError(matches[0])
        time.sleep(1)
    assert document is not None, "document did not become ready within 30 seconds"
    assert document["filename"] == filename
    assert document["chunk_count"] > 0

    status, raw = request(
        f"{API}/chat",
        "POST",
        json.dumps({"question": "InsightHub có những thành phần chính nào?"}).encode(),
        {"Content-Type": "application/json"},
    )
    assert status == 200, status
    chat = json.loads(raw)
    assert chat["answer"].strip()
    assert chat["sources"]
    assert chat["contexts"]
    print(json.dumps({"upload": 202, "document_id": document_id, "status": "ready", "chat": "answer+citation"}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SMOKE_FAILED: {exc}", file=sys.stderr)
        raise
