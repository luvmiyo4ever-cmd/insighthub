# MH10 — test evidence

Collected: `2026-09-28T06:12Z` using the rebuilt pinned ChatOps worker image.

Acceptance-equivalent command (workspace is mounted read-only):

```powershell
docker run --rm -e PYTHONPATH=/workspace/chatops-bot -v "${PWD}:/workspace:ro" -w /workspace insighthub-do2603-chatops-worker:latest pytest -o addopts='' -p no:cacheprovider chatops-bot/tests
```

Output:

```text
28 passed in 1.66s
```

`pytest==8.3.5` is pinned and hash-locked in `chatops-bot/requirements.txt`.
`chatops-bot/pytest.ini` makes the required repository-root command
`pytest chatops-bot/tests` resolve the `app` package when dependencies are
installed. The container command disables only pytest cache because the test
mount is read-only; it does not disable any test.
