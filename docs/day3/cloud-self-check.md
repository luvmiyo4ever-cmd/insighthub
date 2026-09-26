# Cloud self-check before review

All answers must be affirmative before a human approves `aws-plan` or
`aws-apply`. This checklist is intentionally unchecked in the current
workspace.

- [ ] AWS account is a short-lived sandbox and region is recorded.
- [ ] Plan and apply roles are non-admin, distinct, and exact-account scoped.
- [ ] GitHub OIDC trust has exact repository/ref/environment claims; no wildcard.
- [ ] Fork PR workflows cannot request or receive cloud identity.
- [ ] Existing VPC, private subnets, EKS, node security group, domain, and ACM
      certificate were verified read-only.
- [ ] RDS/Redis engine minors and pgvector compatibility are approved.
- [ ] Secret value injection/rotation owner is documented; no secret is in tfvars
      committed to source or uploaded to evidence.
- [ ] Plan artifact is private, source-bound, checksum-verified, and reviewed.
- [ ] Plan contains no unexpected destroy/replacement.
- [ ] Infracost estimate is within the approved budget and assumptions are recorded.
- [ ] Unknown values and IAM/network/data risks are visible in the PR comment.
- [ ] `aws-apply` has named reviewer approval and prevents self-approval.
- [ ] Existing domain/certificate is used; no certificate bypass or public DB/cache.
- [ ] Live namespace, IRSA, RDS, Redis, tags, Helm readiness and migration were verified.
- [ ] HTTPS smoke and Microsoft Edge E2E evidence were collected.
- [ ] Fresh plan was reviewed after smoke.
- [ ] Teardown plan, ownership order, expiry time and cost inventory are ready.

Current result: **STOP — NOT VERIFIED**. No approval, cloud input, saved plan,
live URL, image digest, cost estimate, permission evidence or cleanup inventory
is present in this workspace.
