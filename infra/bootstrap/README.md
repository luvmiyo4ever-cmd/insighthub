# Bootstrap root

This root owns only the encrypted, versioned S3 state bucket and its KMS key.
The bucket uses Terraform's native S3 lockfile (`use_lockfile = true` in the
consumer backend configuration); it does not create a DynamoDB lock table.

The example variables contain placeholders only. A human must review the
bucket name, expiry tag, KMS deletion window, and teardown procedure before an
apply. `force_destroy = false` protects state from accidental deletion.

Static checks:

```powershell
terraform -chdir=infra/bootstrap fmt -check -recursive
terraform -chdir=infra/bootstrap init -backend=false -input=false
terraform -chdir=infra/bootstrap validate
```
