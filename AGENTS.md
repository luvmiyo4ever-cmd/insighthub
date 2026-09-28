# InsightHub - DO2603

InsightHub là RAG Notebook. Day 1 chuyển document ingestion từ synchronous sang asynchronous bằng Redis + ARQ.

## Architecture

* `web/`: Next.js frontend.
* `api/`: FastAPI cho documents, chat, health, metrics.
* `postgres`: PostgreSQL + pgvector.
* `redis`: queue cho ingestion jobs.
* `ingestion-worker/`: ARQ worker xử lý ingestion.
* Ollama là optional profile.

Day 1 mặc định có 5 services:

`web -> api -> redis -> ingestion-worker -> postgres`

`POST /documents` validate file, tạo `pending`, enqueue job và trả HTTP 202.

Worker thực hiện:

`extract -> chunk -> embed -> store -> ready/failed`

## Conventions

* Giữ style và structure hiện tại.
* Reuse `process_document()` thay vì duplicate ingestion logic.
* Configuration lấy từ environment variables.
* API và worker dùng cùng PostgreSQL và Redis.
* Retry phải idempotent, không duplicate chunks.
* Không log secrets hoặc document content.
* Không sửa generated requirements/hash thủ công.
* Review và test AI-generated code trước khi commit.

## Commands

Start:

`docker compose up --build -d --wait`

Check:

`docker compose ps`

`docker compose logs ingestion-worker`

Verify:

`python scripts/verify.py setup`

`python scripts/verify.py smoke --api-url http://localhost:8000 --web-url http://localhost:3000`

Upload:

`curl -X POST http://localhost:8000/documents -F "file=@sample-docs/so-tay-van-hanh.md"`

## Constraints

* `POST /documents` phải trả HTTP 202 nhanh.
* Không chạy ingestion/embedding trong upload request.
* Không gọi `ingest_document_sync()` từ upload handler.
* Worker phải xử lý job qua Redis.
* Retry không được tạo duplicate chunks.
* Worker failure phải cập nhật document thành `failed`.
* Không thay DB schema nếu không cần.
* Không hardcode hoặc commit secrets.
* Không disable tests để verifier pass.
* Ollama không tính vào 5 services Day 1.

Forbidden:

`POST /documents -> ingest_document_sync()`

`REDIS_URL=redis://localhost:6379`

`except Exception: pass`

Hardcoded secrets.

## Domain

Hỗ trợ `.txt`, `.md`, `.pdf`.

Document lifecycle:

`upload -> pending -> ready | failed`

Upload:

1. Validate file.
2. Insert `pending`.
3. Enqueue ARQ job.
4. Return HTTP 202.

Worker:

1. Extract/chunk document.
2. Generate embeddings.
3. Store chunks.
4. Update `ready` hoặc `failed`.

`GET /documents` dùng để theo dõi status.

## References

Ưu tiên:

* `Running-Project-Specification-Student.md` mục 0, 4, 5, 6, 7 là nguồn yêu cầu.
* `docker-compose.yml` - services.
* `api/app/routers/documents.py` - upload contract.
* `api/app/services/ingestion.py` - ingestion logic.
* `api/app/core/config.py` - configuration.
* `infra/db/init.sql` - database schema.
* `ingestion-worker/` - ARQ worker.
* `scripts/` - verifier.

Day 1 completion:

`Compose -> HTTP 202 -> Redis -> Worker -> ready -> Verifier`

## Day 2 - MCP observability

Day 2 dùng Codex/Inspector để kết nối và gọi thật bốn backend MCP: Filesystem, Docker/container, Kubernetes và Prometheus.

* Filesystem chỉ được allow-list `D:\proj\insighthub`.
* Kubernetes dùng ServiceAccount `insighthub/mcp-readonly`, chỉ có verb `get`, `list`, `watch`; không cấp quyền ghi/xóa.
* Prometheus chỉ dùng truy vấn đọc như `list_targets` và instant query.
* Docker chỉ dùng tool đọc container/log; không start, stop, remove hoặc sửa cấu hình.
* Pin version/package/image; không dùng `@latest` trong evidence hoặc cấu hình nộp bài.
* Ghi tool name, input, output, timestamp và screenshot vào `docs/day2/`.
* Không ghi secret, token, kubeconfig hoặc nội dung tài liệu vào evidence.

Day 2 completion:

`4 MCP connected -> read-only calls -> RBAC verified -> evidence -> debug session -> quiz`

## Day 3 - IaC, Kubernetes và cloud review

Day 3 giữ nguyên API, Redis queue, retry, embedding identity và kiến trúc năm
thành phần của Day 1. Kubernetes local phải chạy đủ `web`, `api`,
`ingestion-worker`, Redis và PostgreSQL/pgvector. Kết quả local không phải là
bằng chứng cho AWS. Trên AWS, Redis và PostgreSQL local phải được thay bằng
ElastiCache và RDS; chart AWS không được tạo hai StatefulSet local này.

### Terraform, state và input

* `infra/bootstrap/` sở hữu bootstrap state: S3/KMS và cấu hình backend; dùng
  S3 native lockfile (`use_lockfile = true`), không thêm DynamoDB lock.
* `infra/platform/` sở hữu platform AWS: GitHub OIDC, IRSA, Secrets Manager,
  RDS, ElastiCache, private networking và phần tích hợp EKS cần thiết.
* Không commit `.tfstate`, raw plan, credential, token, secret hoặc file
  `.tfvars` thật. Các `terraform.tfvars.example` chỉ là placeholder không nhạy
  cảm.
* Input nhạy cảm hoặc dependency đã có sẵn phải đi qua GitHub protected
  Environment, chẳng hạn `PLATFORM_TFVARS_B64`, Redis auth token, KMS ARN,
  ARN Lambda rotation, access-log bucket và replica bucket. Không hardcode các
  giá trị này trong source hay PR.
* Destination bucket/policy/KMS cho S3 replication, access-log bucket/policy
  và Lambda rotation là dependency bên ngoài. Source có thể khai báo tích hợp,
  nhưng chỉ AWS evidence mới xác nhận chúng hoạt động.

### OIDC, IRSA và policy gate

* Trust cho GitHub OIDC phải giới hạn theo repository, branch hoặc protected
  Environment cụ thể; không dùng wildcard principal hoặc subject. Plan role và
  apply role tách biệt; apply chỉ nhận saved plan đã review, checksum và source
  binding khớp.
* IRSA phải giới hạn chính xác namespace và ServiceAccount của workload; không
  dùng quyền IAM blanket. PR từ fork không được nhận cloud identity.
* Workflow IaC có đúng bảy job hiển thị: `fmt`, `lint`, `security-scan`,
  `policy-check`, `plan`, `cost-estimate`, `apply`. Các job static chạy trên
  thay đổi IaC; đường cloud là manual và bị chặn bởi protected Environment.
* Không public state, credential hoặc raw plan. PR summary chỉ dùng plan đã
  sanitize: create/change/destroy, rủi ro IAM/network/data, cost và unknown
  values. Dừng trước apply khi input thiếu, checksum/source binding sai, có
  destroy không dự kiến hoặc vượt budget.

### Helm và kiểm chứng

* Chart Day 3 đặt tại `charts/insighthub/`. Local values dùng PostgreSQL/Redis
  trong cluster; AWS values dùng endpoint RDS/ElastiCache, TLS phù hợp và không
  render StatefulSet Redis/PostgreSQL local.
* Giữ probes, resource requests/limits, security context, HPA, Ingress,
  Secrets Store CSI và migration Job trong phạm vi Day 3. Không thêm dashboard,
  alert, ChatOps hoặc security gateway của Day sau.
* Bằng chứng local tối thiểu là pod Ready, `/healthz` HTTP 200, upload
  `/documents` HTTP 202, document `ready` trong không quá 30 giây và `/chat`
  HTTP 200 có answer/citations. Phải ghi rõ fixture mode hay provider thật.
* Bằng chứng AWS chỉ hợp lệ sau protected-environment approval, apply saved
  plan và smoke HTTPS/E2E thực tế. Không ghi local PASS thành cloud PASS.

### Nguồn và trạng thái kiểm chứng

* Nguồn Day 3: `docs/day3/SPEC.md`,
  `docs/day3/verification-matrix.md`, `infra/bootstrap/`, `infra/platform/`,
  `charts/insighthub/` và `.github/workflows/iac.yml`.
* Static checks cần dùng version đã pin: `terraform fmt -check -recursive
  infra`, `terraform init -backend=false`, `terraform validate`, TFLint,
  Checkov và Conftest. Chỉ kết quả run mới được ghi PASS.
* Hiện chỉ được kết luận source/static theo output đã thu thập; không suy diễn
  rằng Checkov, AWS plan/apply, IAM/IRSA, RDS/ElastiCache hoặc HTTPS smoke đã
  PASS nếu chưa có evidence tương ứng.

## Day 4 - Quan sát hệ thống, cảnh báo và MLOps

Day 4 giữ nguyên API, Redis queue, cơ chế retry, embedding identity và kiến
trúc năm thành phần của Day 1. Phần này chỉ bổ sung quan sát Kubernetes cục
bộ; Grafana, Prometheus, Alertmanager và exporter không được tính là thành
phần Day 1.

### Quan sát hệ thống cục bộ đã triển khai

* `charts/insighthub/templates/*servicemonitor*.yaml` thu thập metric của API,
  worker và các dependency/exporter cục bộ qua Prometheus Operator.
* `observability/prometheus-rules.yaml` là nguồn rule độc lập đã kiểm tra bằng
  `promtool`; `charts/insighthub/files/insighthub-anomaly-rules.yaml` là nội
  dung Helm tương ứng cho `PrometheusRule`.
* Recording rule tính giá trị hiện tại, baseline một giờ, độ lệch chuẩn một
  giờ và ngưỡng trên `baseline + 3σ` cho LLM latency p95, độ sâu ARQ queue và
  tỷ lệ HTTP 5xx. Alert rule giữ điều kiện liên tục trong hai phút.
* `tools/grafana/dashboards/insighthub-overview.json` có ít nhất chín panel:
  rate, errors, duration, queue depth, token usage, latency p95, estimated
  cost, pod resources và deployment annotations.
* `observability/alertmanager-slack-local.yaml` chỉ tham chiếu Kubernetes
  secret cục bộ `insighthub-alertmanager-slack`; không bao giờ ghi Slack
  webhook URL vào Git, evidence hoặc log.

### Quy tắc incident theo evidence-first

* Phải chụp baseline Prometheus, trạng thái anomaly/alert và recovery
  **trước** khi viết RCA. Không được mô tả cấu hình dự kiến như một incident
  đã hoàn thành.
* RCA Day 4 phải có `incident_id` khác nhau, `started_at`/`ended_at` RFC3339
  với khoảng thời gian dương, các giả thuyết có nội dung và mẫu Prometheus hữu
  hạn `{metric, labels, timestamp, value}` khớp với telemetry còn lưu. Xem
  `scripts/VERIFICATION_CONTRACT.md`.
* Evidence cục bộ đã hoàn thành hiện có ở
  `rca-reports/incident-2-queue-backlog.json` và
  `rca-reports/incident-3-http-error-burst.json`. RCA latency phải chờ
  baseline một giờ không còn `NaN`; không tạo giả để verifier pass.
* Incident queue phải giữ worker chạy. Dùng hook giới hạn rõ ràng
  `DAY4_CHAOS_WORKER_DELAY_SECONDS`; scale worker về 0 sẽ mất nguồn metric
  queue depth của worker và tạo evidence cũ (stale).
* Hook Day 4 chỉ dùng trong local lab và mặc định không hoạt động. Hook cần
  `DAY4_CHAOS_ENABLED=true`; hook API còn yêu cầu chính xác header
  `X-InsightHub-Chaos`. Phải khôi phục Day 4 values ngay sau khi thu thập
  evidence recovery.

### Nguồn Day 4 và kiểm chứng

* Stack/cấu hình local: `observability/kube-prometheus-stack-local.yaml`,
  `charts/insighthub/values-observability-local.yaml` và
  `charts/insighthub/values-day4-chaos-local.yaml`.
* Kiểm tra rule: `observability/prometheus-rules.test.yaml`; chạy các lệnh đã
  pin `prom/prometheus:v3.7.3` `promtool check rules` và `promtool test rules`
  trong `observability/README.md`.
* Quy trình incident: `scripts/chaos/README.md`.
* Ghi chú MLOps: `docs/day4-mlops-notes.md` (artifact/registry, approval gate,
  drift detection, rollback và ownership).
* Chỉ chạy `python scripts/verify.py day4 --prometheus-url URL` sau khi đã có
  evidence manifest, ba RCA thật và hash tương ứng.

## Day 5 - ChatOps và Incident Response

Day 5 giữ nguyên API, Redis queue, retry, embedding identity và năm thành phần Day 1.

* `chatops-bot` nhận Slack Events qua `/slack/events`, verify raw body, signature và timestamp trước khi parse; từ chối request cũ quá năm phút.
* ACK Slack phải tách khỏi xử lý: event hợp lệ enqueue Redis `arq:chatops`, dedup theo `event_id`; worker dùng retry có giới hạn mới gọi backend và trả lời.
* Chỉ hỗ trợ intent allow-list: health (Prometheus MCP), ingestion hôm nay (API nội bộ fixed origin), pod lỗi (Kubernetes MCP). Không lấy URL, tool, namespace hoặc tham số từ Slack text.
* Kubernetes MCP chỉ đọc và chỉ scope namespace `insighthub`. Audit JSONL persistent tại `/app/audit/chatops-audit.log` chỉ ghi dữ liệu an toàn; không ghi secret, Slack text, document content hoặc raw MCP output.
* Read tự động; `scale api to 1..5` cần approval Redis 60 giây, bind user/action/replicas và one-time. Lệnh destructive bị chặn.
* Scale chỉ qua identity `chatops-mutator`, RBAC namespace chỉ `get`, `patch` `deployments/scale` cho resource `insighthub-api`; không dùng lại Slack secret.
* Evidence local hiện có: MH8 audit, MH9 scale `1→2→1`, MH10 `pytest` 28 pass. MH5/MH6, luồng Slack của MH7 và MH11 chỉ được gọi hoàn thành khi có ảnh hoặc Loom thật.
* Nguồn: `chatops-bot/`, `deploy/chatops-mcp/`, `deploy/chatops-mutator/`, `docs/day5/`.

## Day 6 - Security, Governance & FinOps

* Giữ nguyên API, Redis queue, retry và embedding identity. Không tạo cloud resource từ local.
* Nguồn chính: `security/`, `api/app/services/guardrails.py`, `security/litellm-config.yaml`, `docker-compose*.yml`, `tools/grafana/dashboards/insighthub-overview.json`.
* Đã kiểm chứng local: LiteLLM health, InsightHub gọi qua gateway, Prometheus scrape API/worker/LiteLLM, Grafana panel `LLM Cost (LiteLLM)`.
* Chưa được ghi PASS: final Promptfoo no-HIGH (`redteam-rerun-results.yaml`: 120 cases, 87 pass/33 fail); MH8 thiếu trace thật đủ 3 workload và budget-denied; MH11 AWS Budgets chưa chạy; `red-team-report.html` chưa phải native scan report.
* Should-have CI Promptfoo, prompt/semantic cache, model routing, PII runtime và fallback chỉ ghi PASS khi có evidence tương ứng.
* Không suy diễn từ cấu hình dự kiến; mọi kết luận Day 6 phải kèm output runtime/report thật.
