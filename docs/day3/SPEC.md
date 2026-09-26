# Day 03 IaC SPEC (source-only, local-first)

Status: implementation artifact created for human review. No AWS apply, no
cloud resource creation, and no runtime claim is made by this document.

## Topology and ownership

```text
local Docker Compose (Day 01, unchanged)
  web -> api -> redis -> ingestion-worker -> postgres

AWS bootstrap state
  KMS key -> versioned/private S3 state bucket + native .tflock object

AWS platform
  private RDS PostgreSQL + private ElastiCache Redis
  GitHub OIDC -> exact plan/apply roles
  EKS OIDC -> exact IRSA roles -> exact Secrets Manager ARNs
  Kubernetes namespace -> api/worker ServiceAccounts annotated with IRSA
```

The five Day 01 services, API 202 contract, Redis queue, ARQ retry behavior,
embedding identity, and database schema remain outside this change. Local
Compose is the default test/runtime path. EKS, RDS, ElastiCache, OIDC, and
Secrets Manager are AWS runtime targets and are not represented by local
fixtures.

| State/root | Owns | Does not own |
| --- | --- | --- |
| `infra/bootstrap` | S3 state bucket, versioning, KMS key, bucket policy | VPC, EKS, app data, secret values |
| `infra/platform` | private RDS/Redis, SG, OIDC providers, plan/apply roles, IRSA roles, secret metadata, K8s namespace/ServiceAccounts | secret values, application Deployment/Service/Ingress |

Existing VPC, private subnet IDs, EKS identity, and node security-group IDs
are protected platform inputs. They are pre-existing foundation dependencies,
not resources or a separate Terraform state owned by this repository.

The S3 backend example uses `use_lockfile = true`. No DynamoDB lock table is
created. `force_destroy = false` protects the state bucket during teardown.

## Identity and secret boundaries

- GitHub plan trust is exactly `repo:<owner>/<repo>:pull_request` with
  `aud=sts.amazonaws.com`.
- GitHub apply trust is exactly
  `repo:<owner>/<repo>:ref:refs/heads/<approved-branch>` with the same audience.
- EKS IRSA trust is exactly one namespace/service-account subject per role;
  API and worker are separate.
- No trust policy uses a wildcard subject or principal.
- `aws_secretsmanager_secret` creates metadata only. No
  `aws_secretsmanager_secret_version` is present. RDS manages its master
  password through RDS/Secrets Manager; values are not in source or outputs.
- The apply policy is an explicit, human-reviewed JSON input and is an empty
  placeholder in the example variables file. It must be replaced before any
  apply and cannot contain exact `Action:"*"` or `Resource:"*"` values.

## Managed-service decisions

RDS PostgreSQL and ElastiCache Redis are selected as AWS-managed equivalents
for the local PostgreSQL/pgvector and Redis roles. They are private-only and
reachable from the EKS node security group on ports 5432/6379. RDS is
single-AZ and Redis is one node by default to keep a short lab affordable;
this is not a production availability claim. PostgreSQL extension support,
engine minor versions, and pgvector compatibility require a human review
before plan.

HTTPS termination, ACM certificate ownership, ALB ingress, DNS, and public
application exposure are intentionally deferred. No public ingress is created
in Day 03. An AWS application endpoint must not be called HTTPS-ready until
Day 04-06 supplies an approved certificate/DNS/ALB design and runtime evidence.

## Cost and teardown

Primary cost drivers are RDS instance-hours/storage/backups, ElastiCache
node-hours, EKS/VPC/NAT dependencies if the foundation is not already owned,
KMS/S3 storage, and any later ALB/ACM/DNS or CloudWatch logging. The lab must
have an expiry tag, a named owner, an exact AWS region, and a teardown window.
Do not leave AWS running overnight. Teardown order is: stop workloads, remove
platform resources, verify no dependency remains, then retain/export state for
review before deciding whether to destroy bootstrap state. Bootstrap state is
protected by default.

## Apply stop conditions

Stop before any real plan/apply if any of the following is unresolved:

1. AWS account, region, owner, cost center, expiry, VPC, private subnets, EKS
   cluster, node security group, and GitHub repository are not supplied.
2. Exact RDS/Redis engine minor versions and pgvector compatibility are not
   verified against the target AWS region.
3. GitHub OIDC claims, apply branch protection, required reviewers, and the
   apply policy have not been reviewed.
4. KMS key ownership, Secrets Manager secret-value injection, and rotation
   ownership are not documented.
5. A read-only plan shows public DB/cache ingress, wildcard trust, unexpected
   destroy/replacement, or a cost outside the approved lab budget.
6. HTTPS/DNS/ALB requirements are being assumed even though this Day 03 source
   does not create them.

## Commit strategy

Commit as one reviewable Day 03 change after static gates pass:

1. Terraform source, examples, shared modules, Rego fixtures, and generated
   `.terraform.lock.hcl` files.
2. `docs/day3/SPEC.md`, verification matrix, tool pins, and Checkov exception
   register.
3. Never commit `terraform.tfvars`, provider cache, `.terraform/`, secret
   values, kubeconfig, tokens, or plan files containing sensitive values.

Do not modify Day 01 application files or the pre-existing user modification to
`AGENTS.md` as part of this change.
