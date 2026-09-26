# Platform root

Platform is the reviewed boundary between AWS managed data services, EKS
identity, GitHub OIDC, and Kubernetes service accounts. It creates no secret
value: `aws_secretsmanager_secret` is metadata only, and the RDS password is
managed by RDS. Secret values must be provisioned through an approved runtime
process after this source is reviewed.

The root separates plan and apply roles. Both trust exact OIDC subjects; no
wildcard subject or principal is used. The apply policy is an explicit input,
kept empty in the example, and is a deliberate human-review gate.

Managed services are private-only: RDS and ElastiCache use private subnet IDs,
RDS sets `publicly_accessible = false`, and the data security group permits
ports 5432/6379 only from the EKS node security group. This is a source
contract, not runtime evidence until an approved plan/apply and read-only
checks exist.

Consumer backend example:

```hcl
terraform {
  backend "s3" {
    bucket       = "REPLACE_WITH_BOOTSTRAP_BUCKET"
    key          = "insighthub/platform/terraform.tfstate"
    region       = "REPLACE_WITH_REGION"
    encrypt      = true
    use_lockfile = true
  }
}
```

No apply is part of this change. Review IAM action/resource scope, exact OIDC
claims, engine versions, subnet IDs, KMS choices, and teardown before running
any real plan or apply.
