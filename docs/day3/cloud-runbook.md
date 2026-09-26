# Short-lived AWS sandbox runbook

Status: **NOT VERIFIED**. This runbook is prepared for a protected, approved
AWS sandbox only. It must not be executed with a personal admin identity, a
long-lived access key, or an unreviewed domain/certificate.

## Gate 0: required inputs and approvals

Record these values before starting. Do not put secret values in this file.

| Input | Required evidence | Current status |
|---|---|---|
| Protected `aws-plan` approval | GitHub Environment audit/run URL | NOT VERIFIED |
| Protected `aws-apply` approval | named reviewer approval URL | NOT VERIFIED |
| AWS sandbox account/region | `aws sts get-caller-identity` using plan role | NOT VERIFIED |
| Non-admin plan/apply roles | role ARN and IAM policy review | NOT VERIFIED |
| Existing VPC/private subnets/EKS | read-only describe evidence | NOT VERIFIED |
| Existing domain and ACM certificate | hostname, certificate ARN, ownership evidence | NOT VERIFIED |
| GitHub canonical repository | repository URL and branch protection | NOT VERIFIED |
| Saved plan/source/checksum | private artifact URL and SHA-256 | NOT VERIFIED |
| Budget and expiry | approved USD ceiling and teardown timestamp | NOT VERIFIED |

Stop if any row is missing. A local fixture pass is not cloud evidence.

## Gate 1: source and saved plan binding

Use the exact GitHub run/artifact produced by
`.github/workflows/iac.yml`.

```bash
test "$GITHUB_REPOSITORY" = "$CANONICAL_REPOSITORY"
test "$GITHUB_REF" = refs/heads/main
jq -e --arg repo "$GITHUB_REPOSITORY" --arg sha "$GITHUB_SHA" --arg run "$GITHUB_RUN_ID" \
  '.repository == $repo and .source_sha == $sha and .plan_run_id == $run' \
  plan-artifact/source-binding.json
(cd plan-artifact && sha256sum -c platform.tfplan.sha256)
```

Expected: all checks exit 0. Do not apply if the artifact is from another
commit/run, has a different root, or has a checksum mismatch. Never upload
`terraform.tfstate`, credentials, or raw plan files to a public artifact.

## Gate 2: apply and read-only cloud checks

Apply is performed only by the protected `aws-apply` job, using
`terraform apply` on the verified saved plan. No re-plan is substituted for the
saved plan.

After apply, assume the reviewed non-admin read-only verification role and
collect sanitized output only:

```bash
aws sts get-caller-identity --query '{Account:Account,Arn:Arn}' --output json
aws eks describe-cluster --name "$EKS_NAME" --query 'cluster.{name:name,endpoint:endpoint,oidc:identity.oidc.issuer}' --output json
kubectl config current-context
kubectl -n insighthub get serviceaccounts,deployments,pods
kubectl -n insighthub get serviceaccount api -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
kubectl -n insighthub get serviceaccount ingestion-worker -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}'
aws rds describe-db-instances --db-instance-identifier "$RDS_ID" \
  --query 'DBInstances[0].{id:DBInstanceIdentifier,status:DBInstanceStatus,public:PubliclyAccessible,endpoint:Endpoint.Address,tags:TagList}' --output json
aws elasticache describe-replication-groups --replication-group-id "$REDIS_ID" \
  --query 'ReplicationGroups[0].{id:ReplicationGroupId,status:Status,endpoint:ConfigurationEndpoint.Address,tags:Tags}' --output json
```

Expected: namespace and both ServiceAccounts exist; API/worker IRSA ARNs are
distinct and match the approved roles; RDS is available and not public;
ElastiCache is available and private; tags include Project, Environment, Owner,
CostCenter, ManagedBy, LabId, and ExpiresAt. Redact endpoint hostnames if the
evidence location is public; retain only approved identifiers.

## Gate 3: Helm deployment and HTTPS smoke

Use the reviewed AWS values, never local fixture values. Confirm the AWS values
do not render PostgreSQL or Redis StatefulSets:

```bash
helm lint charts/insighthub -f charts/insighthub/values-staging.yaml
helm template insighthub charts/insighthub -f charts/insighthub/values-staging.yaml \
  --kube-version 1.31.0 > rendered-staging.yaml
! grep -q '^kind: StatefulSet$' rendered-staging.yaml
helm upgrade --install insighthub charts/insighthub \
  -n insighthub --create-namespace \
  -f charts/insighthub/values-staging.yaml \
  --wait --wait-for-jobs --timeout 10m
kubectl -n insighthub get pods -o wide
```

Use the existing domain/certificate only. Record the exact HTTPS URL and ACM
certificate ARN in private evidence. Do not claim HTTPS readiness from an
Ingress manifest alone.

```bash
curl --fail --silent --show-error --location --resolve \
  "$APP_HOST:443:$ALB_IP" "https://$APP_HOST/healthz"
curl --fail --silent --show-error --location --resolve \
  "$APP_HOST:443:$ALB_IP" "https://$APP_HOST/api/health"
```

Expected: TLS certificate hostname matches `$APP_HOST`, health responses are
HTTP 200, and no certificate bypass is used.

## Gate 4: Day 01 request verification and Microsoft Edge E2E

Run the exact Day 01 contract through HTTPS, not a local port-forward:

```bash
curl --fail --silent --show-error -D upload.headers \
  -o upload.json -F "file=@sample-docs/so-tay-van-hanh.md" \
  "https://$APP_HOST/documents"
test "$(awk 'NR==1 {print $2}' upload.headers)" = 202
DOC_ID="$(jq -r .id upload.json)"
python scripts/verify.py smoke --api-url "https://$APP_HOST" --web-url "https://$APP_HOST"
```

Record the exact document ID, pending-to-ready duration (must be <=30s), chat
answer, and citation/source IDs. Do not store document content or bearer tokens.

Microsoft Edge must be used for the UI evidence. Record the Edge version,
visible HTTPS URL, upload result, Ready result, chat answer/citations, and a
DevTools Console export with no errors. If Edge automation or console access is
unavailable, mark this gate `NOT VERIFIED`; do not substitute the Codex browser
or a local HTTP test and call it Edge evidence.

## Gate 5: fresh plan and teardown

After runtime checks, create a fresh read-only plan with the same approved
non-admin plan role. Store only sanitized JSON/Markdown and checksum in private
evidence.

```bash
terraform -chdir=infra/platform plan -input=false -no-color -detailed-exitcode \
  -var-file=terraform.tfvars -out=fresh.tfplan
terraform show -json fresh.tfplan > fresh.plan.json
sha256sum fresh.tfplan > fresh.tfplan.sha256
```

Expected: no unexpected destroy/replacement. Any drift, unknown ownership,
public data path, or budget overrun stops teardown review until a human decides.

Teardown by ownership, in this order:

1. Remove Helm release, Ingress/LoadBalancer, and application workloads.
2. Confirm no Kubernetes Service/Ingress still owns an AWS load balancer.
3. Destroy `infra/platform` using a reviewed destroy plan and the platform owner.
4. Do not destroy bootstrap state until state export/retention is reviewed.
5. Re-run read-only inventory and confirm no billable platform resources remain.

Final cost inventory must include resource ID, owner/state root, region, status,
hourly/monthly cost assumption, and evidence timestamp for EKS dependency,
RDS, ElastiCache, NAT/public IPv4, ALB, EBS/snapshots, KMS, S3, and telemetry.

## Evidence publication rule

Public evidence may contain only sanitized counts, status, timestamps, source
SHA, image digests, and redacted URLs. Keep state, raw plans, tfvars, kubeconfig,
tokens, secret values, document content, and private endpoints in restricted
storage. Every unchecked item remains `NOT VERIFIED`.
