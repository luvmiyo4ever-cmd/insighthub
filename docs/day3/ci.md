# Day 03 CI and reviewed cloud execution

## Workflow split

`ci.yml` runs on push and pull request. It has no `id-token` permission and
does not configure AWS credentials. It covers workflow contracts, Terraform
format/validate/TFLint, strict Checkov, positive/negative Conftest fixtures,
Day 01 application tests, and local image builds without push.

`iac.yml` is `workflow_dispatch` only. It is fail-closed to the
canonical repository, `main`, a private repository, a protected `aws-plan`
environment, and a protected `aws-apply` environment. The plan role and apply
role are separate protected variables. A fork cannot satisfy the canonical
repository condition and therefore cannot receive cloud identity from this
workflow.

## Required protected configuration

Repository/environment variables:

- `CANONICAL_REPOSITORY`, `AWS_REGION`, `AWS_ACCOUNT_ID`
- `PLAN_ROLE_ARN`, `APPLY_ROLE_ARN`
- `OPENAI_MODEL`

Environment secrets:

- `PLATFORM_TFVARS_B64` in both environments, containing reviewed non-committed
  Terraform variables; it must not be printed or uploaded.
- `INFRACOST_API_KEY` in `aws-plan`.
- `OPENAI_API_KEY` in `aws-plan`.

`aws-apply` must require named reviewers and prevent self-approval. The AWS
roles must trust only the exact GitHub OIDC subjects documented in
`docs/day3/SPEC.md`; no wildcard subject or principal is acceptable.

## Plan/apply boundary

The plan job writes a Terraform saved plan only in the runner workspace, creates
an SHA-256 checksum, binds it to repository/source SHA/run ID, and uploads it
only after asserting that the repository is private. The apply job downloads
that artifact, verifies binding and checksum, initializes the same backend, and
uses `terraform apply` on that exact file. It never replans before apply.

The sanitized comment includes create/change/destroy counts, IAM/network/data
risk, Infracost estimate and budget status, unknown-value count, and a human
review conclusion. The AI step receives only the sanitized summary and uses
the OpenAI Responses API with `store=false`; raw plan, Terraform state,
credentials, and secret values are not sent.

Apply stops before the protected approval gate when cloud input is missing,
the repository/ref is wrong, the budget is missing or exceeded, the plan has
unexpected destroy/replacement, the source binding does not match, or the
checksum fails. Unknown computed values remain visible in the review and still
require human review.

## Current verification state

No cloud inputs, protected variables, secrets, GitHub run, saved plan, AWS
identity, cost estimate, PR comment, or apply was available in this workspace.
The local check is limited to workflow contract validation and Python syntax;
actual GitHub Actions execution remains pending human configuration/review.
