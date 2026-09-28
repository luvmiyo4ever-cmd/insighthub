# Day 5 local MCP backends

These two manifests expose the existing Day 2 Kubernetes and Prometheus
backends using Streamable HTTP inside the local `docker-desktop` cluster. They
are ClusterIP-only: do not expose either MCP service through the Slack/ngrok
endpoint.

The Kubernetes backend runs with the existing `insighthub/mcp-readonly`
ServiceAccount and server-side `read_only = true`. Its tool allowlist contains
only `pods_list_in_namespace`, and the ChatOps worker always passes the fixed
`insighthub` namespace. The Prometheus backend has no Kubernetes API token and
reads only the in-cluster Prometheus Service.

Apply only to the local lab:

```powershell
kubectl apply -f deploy/chatops-mcp/kubernetes-mcp.yaml
kubectl apply -f deploy/chatops-mcp/prometheus-mcp.yaml
kubectl apply -f deploy/chatops-mcp/kubernetes-api-egress-local.yaml
kubectl -n insighthub rollout status deployment/chatops-kubernetes-mcp
kubectl -n insighthub rollout status deployment/chatops-prometheus-mcp
```

`kubernetes-api-egress-local.yaml` is only for the current Docker Desktop
cluster. It allows the Kubernetes MCP pod to reach the verified local API
endpoint (`172.19.0.5:6443`) and must not be reused for another cluster.

The Compose worker reaches the ClusterIP services through two local,
operator-run port forwards. Keep both terminals open while testing Slack:

```powershell
kubectl -n insighthub port-forward svc/chatops-kubernetes-mcp 18081:8080
kubectl -n insighthub port-forward svc/chatops-prometheus-mcp 18082:8080
```

Set the following ignored root `.env` values, then recreate `chatops-worker`:

```dotenv
MCP_KUBERNETES_URL=http://host.docker.internal:18081/mcp
MCP_PROMETHEUS_URL=http://host.docker.internal:18082/mcp
```

Never add a kubeconfig, Kubernetes bearer token, Slack token, or an MCP public
URL to this directory or to evidence.
