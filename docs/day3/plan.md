# Day 03 execution plan (not an apply plan)

1. Human reviews `SPEC.md`, exact provider/tool pins, AWS account/region,
   existing foundation IDs, GitHub repository/branch, apply policy, engine
   minor versions, KMS ownership, and cost ceiling.
2. Run formatting, backend-disabled init, validate for bootstrap/platform,
   TFLint, Checkov, and the Conftest positive/negative assertions.
3. Review Checkov exceptions and either update the approved SPEC or record an
   explicit acceptance. Do not use a blanket skip.
4. Only after that review, configure backend HCL and non-committed values for a
   read-only Terraform plan. Inspect detailed exit code, IAM trust, network
   reachability, replacement/destroy actions, and estimated cost.
5. A separate human approval is required before any apply role can be used.
   Apply is outside this turn and must be followed by read-only runtime
   evidence plus teardown before the expiry window.

## Inputs still missing

- AWS account ID, region, budget/alert, owner, cost center, and expiry time.
- Existing VPC ID, private subnet IDs, EKS name/endpoint/CA/OIDC issuer, and
  EKS node security-group ID.
- GitHub owner/repository, protected apply branch/environment, required
  reviewers, OIDC thumbprint/claim evidence, and the reviewed apply policy.
- Exact RDS/Redis engine minors, existing KMS key ARNs, provider secret ARNs,
  database username, and the secret-value injection/rotation owner.
- ACM certificate/DNS/ALB design if HTTPS is required in a later day.

## Deliberately out of scope

No AWS apply, no long-lived credentials, no public DB/cache, no DynamoDB lock,
no application Deployment/Service/Ingress/ALB/ACM/DNS, no secret version, no
Terraform plan file, and no changes to Day 01 application behavior.
