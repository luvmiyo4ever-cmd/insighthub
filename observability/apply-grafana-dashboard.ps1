param(
    [string]$Namespace = "monitoring"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dashboard = Join-Path $root "tools/grafana/dashboards/insighthub-overview.json"

if (-not (Test-Path -LiteralPath $dashboard)) {
    throw "Dashboard source not found: $dashboard"
}

# Grafana's kube-prometheus-stack sidecar watches this label across namespaces.
kubectl -n $Namespace create configmap insighthub-grafana-dashboard `
    --from-file=insighthub-overview.json=$dashboard `
    --dry-run=client -o yaml |
    kubectl apply -f -
kubectl -n $Namespace label configmap insighthub-grafana-dashboard `
    grafana_dashboard=1 --overwrite
