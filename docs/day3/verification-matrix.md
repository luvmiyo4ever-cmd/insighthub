# Day 03 verification matrix

All results below are source/static checks unless explicitly marked runtime.
Passing `validate`, TFLint, Checkov, or Conftest does not prove AWS resources
exist or that an IAM/Kubernetes action works in a live account.

| Requirement | Artifact/source | Verify command | Expected result |
| --- | --- | --- | --- |
| Exact Terraform/provider pins | `infra/*/providers.tf`, child `versions.tf` | `terraform -chdir=infra/<root> init -backend=false -input=false` | exit 0; matching `.terraform.lock.hcl` with checksums |
| Formatting | all `infra/**/*.tf` | `terraform -chdir=infra fmt -check -recursive` | exit 0 |
| Bootstrap syntax | `infra/bootstrap` | `terraform -chdir=infra/bootstrap validate` | “configuration is valid” |
| Platform syntax | `infra/platform` | `terraform -chdir=infra/platform validate` | “configuration is valid” |
| S3 native lockfile | `infra/bootstrap/README.md`, backend examples | inspect backend for `use_lockfile = true`; later read-only backend check | no DynamoDB lock resource; live lock check still pending |
| State protection | `infra/bootstrap/main.tf` | Checkov + source review | versioning, SSE-KMS, public access block, TLS deny, `force_destroy=false` |
| Standard tags | `infra/modules/standard-tags` | Checkov + source review | Project/Environment/Owner/CostCenter/ManagedBy/LabId/ExpiresAt defined |
| Exact GitHub OIDC trust | `infra/platform/main.tf` | source review; later IAM read-only policy fetch | exact repo/environment subjects and `aud=sts.amazonaws.com`; runtime pending |
| Exact IRSA trust | `infra/platform/main.tf` | source review; later IAM/EKS read-only check | exact namespace/service-account subjects; runtime pending |
| No secret value in source | platform secret resource and examples | `rg -n "secret_version|password\s*=|token\s*=|AKIA|BEGIN PRIVATE" infra` | no credential value; example placeholders only |
| Private data path | RDS/Redis SG, subnet groups | Checkov + source review; later AWS describe | no public DB/cache ingress; runtime pending |
| Rego positive fixture | `infra/policies/tests/positive-plan.json` | `conftest test -p infra/policies infra/policies/tests/positive-plan.json` | exit 0; all tests pass |
| Rego negative fixture | `infra/policies/tests/negative-plan.json` | same command, assert `$LASTEXITCODE -eq 1` | non-zero denial is expected and asserted; not soft-failed |
| TFLint | tool pin doc + Terraform source | `tflint --chdir=infra --recursive` | exit 0 |
| Checkov | tool pin doc + Terraform source | `checkov -d infra --framework terraform --quiet` | current source scan is non-zero with documented exceptions; no skips |
| Local/AWS separation | SPEC and roots | inspect protected foundation inputs and `infra/platform` resources | local fixture values never claim AWS runtime evidence |
| HTTPS boundary | SPEC | source review | no public HTTPS claim; ALB/ACM/DNS deferred |
| Teardown readiness | tags, README, SPEC | review expiry/cost/ownership and `force_destroy=false` | human approval required before apply |

## Current observed results

- Terraform 1.15.8, AWS 6.61.0, TLS 4.4.1, and Kubernetes 3.2.1 initialized
  with backend disabled. Lockfiles were generated; no AWS API plan/apply ran.
- `fmt -check` and both root `validate` commands pass.
- TFLint 0.64.0 passes recursively with no issues.
- Conftest 0.69.0 / OPA 1.19.0: positive fixture passes; negative fixture
  returns the expected exit code 1 with explicit denials.
- Checkov 3.3.19: 140 passed, 15 failed, 0 skipped. Its optional online
  guideline lookup was unreachable in the sandbox; local Terraform checks
  still executed. The 15 failures are recorded below rather than skipped.

## Checkov exceptions requiring review

| Check(s) | Reason not silently skipped | Required decision |
| --- | --- | --- |
| CKV_AWS_356 | AWS Describe/List APIs commonly require `Resource:"*"`; this statement is read-only and separate from exact state object permissions | IAM reviewer confirms action list and no mutation |
| CKV_AWS_129, CKV2_AWS_30 | RDS logs add CloudWatch cost and retention/handling requirements not approved for this short lab | decide logging destination/retention before apply |
| CKV_AWS_118 | Enhanced monitoring requires a monitoring role and additional telemetry cost | approve role/cost or keep deferred |
| CKV_AWS_161 | IAM DB authentication would change the existing app credential/connection contract | application owner must approve a separate auth migration |
| CKV_AWS_293 | Deletion protection conflicts with short-lived teardown; final snapshot remains default-on | human must approve the teardown window |
| CKV_AWS_353 | Performance Insights can add cost and is not needed for the Day 03 source gate | approve observability scope |
| CKV_AWS_191 | Redis uses encryption flags but no customer-managed KMS key by default to avoid creating/owning another key in a short lab | choose an existing reviewed CMK or accept AWS-managed encryption |
| CKV_AWS_31 | Redis auth token handling must not put a secret in tfvars/state and is not wired into the Day 01 queue contract | design secret injection and app configuration first |
| CKV2_AWS_50 | Multi-AZ/automatic failover needs more cache nodes and increases cost; default is one node | approve availability/cost tradeoff |
| CKV2_AWS_57 | Secret rotation needs an owner, rotation Lambda, and an application reload plan | assign rotation owner before production use |
| CKV2_AWS_62 | State bucket notifications are not required for the lock protocol and would add an unapproved destination | define evidence/alert destination if required |
| CKV_AWS_18 | Access logging needs a separate log bucket and retention policy | approve separate log ownership/cost |
| CKV_AWS_144 | Cross-region replication doubles storage/transfer and conflicts with local-first short lab | approve DR budget and second-region ownership |

These are exceptions to the current short-lab design, not evidence that the
checks are satisfied. No Checkov skip configuration is committed.
