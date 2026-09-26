# Helm/kind verification

Date: 2026-09-24

## Scope

This check covers the Day 01 five-component contract only:

`web -> api -> redis -> ingestion-worker -> postgres`

The local profile uses fixture providers and PostgreSQL/Redis StatefulSets in
the kind cluster. The `dev` and `staging` profiles set provider mode to real,
enable the AWS Secrets Store CSI integration, and disable both local
StatefulSets. Their RDS/ElastiCache endpoints and provider secrets are
placeholders until a reviewed AWS environment is supplied. No AWS apply was
performed.

No dashboard, alert, ChatOps, or security-gateway resources are in this chart.

## Static verification

Commands run:

```powershell
helm lint charts/insighthub -f charts/insighthub/values-local.yaml
helm lint charts/insighthub -f charts/insighthub/values-dev.yaml
helm lint charts/insighthub -f charts/insighthub/values-staging.yaml
helm template insighthub charts/insighthub -f <values> --kube-version 1.31.0
python -m py_compile scripts/kind_smoke.py
```

Observed results:

| Profile | Helm lint | Rendered local StatefulSets | Other rendered evidence |
|---|---:|---:|---|
| local | PASS (0 failed) | 2 | fixture mode; PostgreSQL and Redis enabled |
| dev | PASS (0 failed) | 0 | `SecretProviderClass` 1; `Ingress` 1 |
| staging | PASS (0 failed) | 0 | `Ingress` 1; AWS-backed values expected |

The Helm icon message is informational only. Render success is static evidence;
it does not prove that a provider, CSI driver, RDS, ElastiCache, or ingress
controller exists at runtime.

The local render contains 3 Deployments, 5 Services, 1 migration Job, 5
readiness probes, and non-root security contexts. HPA is intentionally disabled
for the one-replica local fixture; dev and staging each render 2 HPAs. This is
chart evidence, not a metrics-server or autoscaling runtime result.

## kind runtime attempt

The separate cluster `insighthub-lab` was created with `kind/insighthub.yaml`.
The script created the local namespace and generated the runtime secret without
committing credentials. API and web images built successfully, but loading the
API image into kind failed because the host temporary directory on C: had no
free space. The later retry using a D: temporary directory could not continue
because Docker Desktop stopped and reported `Docker Desktop is unable to
start`.

Therefore the following are **NOT VERIFIED** and must not be reported as pass:

- all five pods Ready;
- `/healthz`, `/readyz`, and web health HTTP 200;
- exact document upload HTTP 202;
- document reaching `ready` within 30 seconds;
- chat answer with citations;
- browser console free of errors;
- migration Job completion.

The requested teardown was attempted with:

```powershell
scripts/kind-lab.ps1 down
```

It failed for the same Docker Desktop start error. The next operator action is
to restore Docker Desktop, run the command above, and verify that
`kind get clusters` no longer lists `insighthub-lab` before another lab run.

## UI evidence

Microsoft Edge is installed on the host, but the available computer-use surface
exposed no Edge app/window (only the Codex in-app browser). Consequently no Edge
navigation or console evidence was collected. This is an environment evidence
gap, not a successful UI check.

## Runtime cleanup rule

Do not run AWS apply or create provider resources to complete this check. After
Docker recovery, rerun only the local `kind-lab.ps1 up`, `kind-smoke.ps1`, and
`kind-lab.ps1 down` flow. Keep AWS values as render-only until OIDC, IRSA,
Secrets Manager, RDS, ElastiCache, ingress/HTTPS, and cost approvals are
reviewed.
