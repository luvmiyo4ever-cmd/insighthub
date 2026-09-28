# Observability và MLOps - bắt buộc Day 4

ServiceMonitor/exporters cho đủ5 thành phần, Grafana9+ panels,3 anomaly và3 incident/RCA, Slack alert, MLOps overview notes4 blocks/quiz. Queue/worker Day 1 và deployment Day 3 phải có thật. [Spec mục 8](../Running-Project-Specification-Student.md).

Dùng telemetry local cho baseline; không giữ AWS chạy liên tục. Alloy/OTel có thể cải tiến collector, không bỏ các nhiệm vụ gốc.
## Day 4 anomaly bands

`prometheus-rules.yaml` is the standalone `groups:` source validated by
promtool. The Helm chart wraps the same rule payload as a `PrometheusRule` for
the Prometheus Operator. It records a current value, 1-hour baseline,
1-hour standard deviation and `baseline + 3σ` upper band for LLM latency p95,
ARQ queue depth, and HTTP 5xx ratio.

The Helm chart packages the equivalent rule payload and applies it only when
`observability.rules.enabled=true`. The local overlay sets the required
`release: kube-prometheus-stack` selector label and deploys the resource to
`monitoring`.

Validate source rules before applying:

```powershell
docker run --rm -v "${PWD}/observability:/rules:ro" prom/prometheus:v3.7.3 `
  promtool check rules /rules/prometheus-rules.yaml
docker run --rm -v "${PWD}/observability:/rules:ro" prom/prometheus:v3.7.3 `
  promtool test rules /rules/prometheus-rules.test.yaml
```

`kube-prometheus-stack-local.yaml` enables Grafana only in the Docker Desktop
lab. Its sidecar discovers ConfigMaps labelled `grafana_dashboard: "1"` across
the cluster; it is not an AWS deployment configuration.

Apply the version-controlled dashboard JSON to the local Grafana sidecar:

```powershell
./observability/apply-grafana-dashboard.ps1
```
