# Prometheus MCP Evidence

## Connection details

- Server: `prometheus`
- Configured image/version: `ghcr.io/tjhop/prometheus-mcp-server:v0.18.0` (from the MCP configuration shared earlier)
- Transport: `stdio` (server launched with Docker stdio)
- Prometheus URL configured for the server: `http://host.docker.internal:9090`
- Codex version / exact MCP call timestamp: not captured

## Successful read-only calls

### List scrape targets

- Tool: `list_targets`
- Input: `{}`

Output:

```json
{
  "activeTargets": [
    {
      "job": "insighthub-api",
      "instance": "api:8000",
      "health": "up",
      "lastError": "",
      "lastScrape": "2026-09-22T12:59:08.445310862Z"
    },
    {
      "job": "prometheus",
      "instance": "localhost:9090",
      "health": "up",
      "lastError": "",
      "lastScrape": "2026-09-22T12:58:58.725025819Z"
    }
  ],
  "droppedTargets": []
}
```

### Instant query `up`

- Tool: `query`
- Input: `{"query":"up"}`

Output:

```text
up{instance="api:8000", job="insighthub-api"} => 1 @1790081948.861
up{instance="localhost:9090", job="prometheus"} => 1 @1790081948.861
warnings: null
```

At the evaluation timestamp returned, both targets had `up = 1`.

- Inspector screenshot: not captured
