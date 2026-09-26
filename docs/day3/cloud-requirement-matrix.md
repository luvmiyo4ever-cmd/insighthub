# Cloud requirement matrix

Status convention: `PASS` requires live evidence from the approved AWS sandbox;
`STATIC` is source/workflow evidence only; `NOT VERIFIED` means no live evidence
was collected. Local fixture results never upgrade a cloud row.

| Requirement | Artifact/source | Verify command or evidence | Expected | Current status |
|---|---|---|---|---|
| Protected environment approval | GitHub `aws-plan`/`aws-apply` settings | Environment audit/run URL | named reviewers, no self-approval | NOT VERIFIED |
| Non-admin identity | workflow role vars and IAM | `aws sts get-caller-identity` | approved plan/apply ARN, account matches | NOT VERIFIED |
| Fork isolation | `iac.yml` | inspect job conditions; fork test run | no `id-token` job runs for fork | STATIC |
| Saved plan binding | artifact `source-binding.json` | `jq` binding check + `sha256sum -c` | source/run/root/checksum match | NOT VERIFIED |
| Namespace | Helm/platform output | `kubectl -n insighthub get ns` | namespace exists | NOT VERIFIED |
| API IRSA | `infra/platform/main.tf` | ServiceAccount annotation + IAM trust | exact API subject/role | NOT VERIFIED |
| Worker IRSA | `infra/platform/main.tf` | ServiceAccount annotation + IAM trust | exact worker subject/role | NOT VERIFIED |
| RDS | platform Terraform | `aws rds describe-db-instances` | available, private, approved tags | NOT VERIFIED |
| ElastiCache | platform Terraform | `aws elasticache describe-replication-groups` | available, private, approved tags | NOT VERIFIED |
| Standard tags | `infra/modules/standard-tags` | AWS tag inventory | required seven tags on owned resources | NOT VERIFIED |
| AWS Helm values | `values-staging.yaml` | Helm render | no PostgreSQL/Redis StatefulSet | STATIC |
| Helm deployment | chart | `helm upgrade --install --wait` | pods Ready and migration complete | NOT VERIFIED |
| HTTPS certificate | existing domain/ACM input | `openssl s_client`, `curl --resolve` | hostname/certificate match, HTTP 200 | NOT VERIFIED |
| Upload contract | Day 01 API | HTTPS `POST /documents` | exact HTTP 202 | NOT VERIFIED |
| Async Ready | Day 01 worker | poll exact document ID | `ready` within 30 seconds | NOT VERIFIED |
| Chat/citations | Day 01 API | HTTPS `POST /chat` | answer and citations present | NOT VERIFIED |
| Edge E2E | Microsoft Edge | Edge URL/upload/chat/console evidence | no console errors | NOT VERIFIED |
| Permission allow/deny | plan/apply/read-only roles | IAM policy simulation or reviewed denial evidence | allowed actions only; mutation denied to read-only role | NOT VERIFIED |
| Fresh plan | saved source + backend | `terraform plan -detailed-exitcode` | no unexpected destroy/drift | NOT VERIFIED |
| Cost assumptions | Infracost + AWS pricing evidence | PR comment and cost inventory | create/change/destroy, unknowns, budget | NOT VERIFIED |
| Teardown ownership | state roots and inventory | reviewed destroy plan + post-delete inventory | no owned billable resource remains | NOT VERIFIED |
