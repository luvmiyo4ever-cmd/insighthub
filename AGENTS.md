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

* `Running-Project-Specification-Student.md` - source of truth.
* `docker-compose.yml` - services.
* `api/app/routers/documents.py` - upload contract.
* `api/app/services/ingestion.py` - ingestion logic.
* `api/app/core/config.py` - configuration.
* `infra/db/init.sql` - database schema.
* `ingestion-worker/` - ARQ worker.
* `scripts/` - verifier.

Day 1 completion:

`Compose -> HTTP 202 -> Redis -> Worker -> ready -> Verifier`
