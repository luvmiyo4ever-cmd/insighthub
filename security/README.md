# Security, Governance, FinOps - bắt buộc Day 6

Học viên hoàn thiện Promptfoo50+ cases, initial/final reports, guardrails runtime, LiteLLM gateway+3 virtual keys/budgets, routing cho app/bot/coding agent, cost dashboard và threat model>=6 threats. [Spec mục10](../Running-Project-Specification-Student.md).

`promptfooconfig.yaml`, `coverage-mapping.yaml` và
`rag-upload-retrieve-provider.mjs` là cấu hình/adapter đang được scan cho
MH1-MH2; chúng không tự chứng minh scan, no-HIGH, guardrails hoặc runtime
 integration. `rag-boundary-plugin.yaml` và `indirect-rag-plugin.yaml` là
 custom-plugin cho grader RAG chạy thật bằng Ollama local. Plugin built-in
 indirect của Promptfoo 0.123.1 cần biến `context` mà adapter upload/retrieve
 không xuất ra, nên không dùng plugin built-in đó làm runtime grader cho target này.

`red-team-report.html` là artifact/report contract cho MH3 nhưng hiện giữ trạng
thái `NOT RUN / INCOMPLETE`; không coi file này là scan evidence. Initial report
chỉ được kết luận sau khi `promptfoo redteam run` tạo output có test cases và
provider responses thật.

Cấu hình dùng plugin file riêng và Promptfoo được pin ở `package.json`. Sau khi
tạo lockfile trong môi trường tool riêng, chạy từ repository root:

```bash
npm ci --prefix security --ignore-scripts
npx --prefix security promptfoo@0.123.1 redteam generate -c security/promptfooconfig.yaml
```

Để chạy không cần OpenAI API, bật Ollama profile và tải model local nhỏ:

```bash
docker compose --profile ollama up -d ollama
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama list
```

`promptfooconfig.yaml` dùng `ollama:chat:qwen2.5:3b` cho generator/grader của
Promptfoo. Đây là model của evaluator, không thay đổi `LLM_PROVIDER` hoặc
embedding identity của InsightHub.

Để thực hiện MH3, chạy scan hai bước bằng lệnh pin version:

```bash
npx --prefix security promptfoo@0.123.1 redteam run \
  -c security/promptfooconfig.yaml \
  -o security/redteam-initial.yaml \
  --strict --no-progress-bar
```

Sau đó xuất/review report native của Promptfoo và cập nhật
`red-team-report.html`; không dùng scaffold hiện tại làm bằng chứng scan.

MH2 được map trong `coverage-mapping.yaml`. Direct injection, PII và excessive
agency đi qua target HTTP `/chat`; indirect injection và RAG poisoning đi qua
`rag-upload-retrieve-provider.mjs`, adapter gọi đúng flow `POST /documents`
(202), poll `GET /documents`, rồi `POST /chat`. Adapter không được chạy trong
thay đổi này nên chưa tạo runtime evidence và không dọn các fixture sau khi
chạy.

Khi Promptfoo chạy trên Windows host, adapter mặc định dùng
`http://127.0.0.1:8000`; có thể ghi đè bằng `INSIGHTHUB_REDTEAM_URL` nếu
`API_PORT` khác 8000. Mỗi request có timeout 10 giây để endpoint không khả dụng
không làm scan treo lâu.

Các plugin phải giữ đúng ID của Promptfoo 0.123.1. Bản pin này liệt kê
`rag-poisoning` nhưng evaluation runtime không đăng ký grader tương ứng, nên
scan dùng `rag-boundary-plugin.yaml` làm grader executable và ghi limitation
trong mapping. Khi chạy thật, dùng Compose local và review output trước khi kết
luận MH3-MH5; không coi `status: configured` trong mapping là PASS. Nguồn: [red-team configuration](https://www.promptfoo.dev/docs/red-team/configuration/),
[indirect prompt injection](https://www.promptfoo.dev/docs/red-team/plugins/indirect-prompt-injection/),
[custom API provider](https://www.promptfoo.dev/docs/providers/custom-api/),
[RAG red teaming](https://www.promptfoo.dev/docs/red-team/rag/).
