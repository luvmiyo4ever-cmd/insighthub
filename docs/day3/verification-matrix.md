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
- Checkov 3.3.19 baseline: 140 passed, 15 failed, 0 skipped. The RDS and IAM
  source has subsequently been tightened; a fresh Checkov run is still
  required before any of those findings can be marked passed.

## Checkov findings pending a fresh scan

| Check(s) | Reason not silently skipped | Required decision |
| --- | --- | --- |
| CKV_AWS_356, CKV_AWS_129, CKV2_AWS_30, CKV_AWS_118, CKV_AWS_161, CKV_AWS_157, CKV_AWS_293, CKV_AWS_353 | Remediation is present in source: exact IAM reads, PostgreSQL log export/parameter group, Enhanced Monitoring, IAM DB auth, Multi-AZ, deletion protection, and Performance Insights | rerun pinned Checkov and review plan/cost before declaring pass |
| CKV_AWS_191, CKV_AWS_31, CKV2_AWS_50 | Remediation is present: exact CMK input, protected Redis AUTH token, two nodes, Multi-AZ, and automatic failover | fresh Checkov plus runtime TLS/AUTH/failover evidence; update AWS Helm secret injection before deploy |
| CKV2_AWS_57 | Rotation schedule and Lambda invoke permission are present | provide an existing reviewed, provider-specific rotation Lambda; AWS must successfully run its test rotation |
| CKV2_AWS_62, CKV_AWS_18, CKV_AWS_144 | State bucket has EventBridge notification, access-log destination, and SSE-KMS cross-region replication configuration | provide pre-owned log/replica buckets and destination KMS policy; verify replication after apply |

These source changes are not evidence that the checks or their external
dependencies are satisfied. No Checkov skip configuration is committed.
