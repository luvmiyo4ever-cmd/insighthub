# PR: reviewed AWS sandbox deployment path

## Summary

- Adds a fail-closed GitHub Actions path for reviewed Terraform plan/apply.
- Keeps PR/fork CI local-only with no OIDC permission.
- Binds a private saved plan to source SHA, run ID, root and SHA-256 checksum.
- Produces sanitized Infracost/risk/unknown-value review and optional AI
  explanation without sending raw plan, state, credentials or document content.
- Adds the short-lived AWS verification, HTTPS, Edge E2E and teardown runbook.

## Safety boundaries

- No AWS apply was run by this change.
- No personal admin credential is accepted or stored.
- Plan/apply roles are separate and must be configured as non-admin protected
  variables in GitHub.
- `aws-apply` must be protected with named reviewers and no self-approval.
- Public repositories and forks fail preflight before any OIDC job runs.
- Apply uses only the reviewed saved plan after source/checksum verification.
- Unexpected destroy/replacement, missing inputs, checksum mismatch, or budget
  overrun stops the run.

## Verification

| Check | Result |
|---|---|
| YAML parse | PASS (local) |
| actionlint | PASS (v1.7.12, checksum verified) |
| workflow contract | PASS (local) |
| Python helper compile | PASS (local) |
| AWS plan/apply | NOT VERIFIED — no approved cloud input/run |
| Live namespace/IRSA/RDS/Redis/tags | NOT VERIFIED |
| Helm live deployment | NOT VERIFIED |
| HTTPS smoke | NOT VERIFIED |
| Microsoft Edge E2E/console | NOT VERIFIED |
| Fresh plan | NOT VERIFIED |
| Teardown/cost inventory | NOT VERIFIED |

## Required review inputs

Provide protected Environment approval, canonical repository variables, exact
plan/apply role ARNs, sandbox account/region, private state bucket/key, reviewed
Terraform variables, existing domain/ACM certificate, budget ceiling, expiry,
and the GitHub run/artifact URL. Do not paste credentials, state, raw plan, or
secret values into this PR.

## Live evidence placeholders

- PR URL: `NOT PROVIDED`
- Plan run URL: `NOT PROVIDED`
- Apply run URL: `NOT PROVIDED`
- HTTPS live URL: `NOT PROVIDED`
- Source SHA: `NOT PROVIDED`
- API/worker image digests: `NOT PROVIDED`
- Infracost comment: `NOT PROVIDED`
- Cleanup inventory: `NOT PROVIDED`
