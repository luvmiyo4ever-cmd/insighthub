# Day 2 MCP Evidence

Thư mục này chứa bằng chứng review được cho bốn MCP backend bắt buộc của Day 2.

## Quy tắc ghi evidence

- Thay mọi giá trị `<...>` bằng output thật từ host Codex/Inspector hoặc CLI.
- Ghi thời gian RFC3339 có timezone, host, server/version, transport và môi trường.
- Không ghi API key, token, kubeconfig, `.env`, Docker credential hoặc document content.
- Tool name phải là tool thật được server expose; không dùng tên minh họa nếu khác thực tế.
- Lưu screenshot Inspector tương ứng với từng backend trong thư mục này.
- `node tools/mcp/smoke.mjs` chỉ chứng minh MCP starter, không thay thế evidence của bốn backend.

## Checklist

- [ ] `filesystem.md`: đọc trong project và bị từ chối ngoài allow-list.
- [ ] `docker.md`: gọi tool đọc container/log và có case debug thực tế.
- [ ] `kubernetes.md`: gọi tool đọc pod và chứng minh RBAC `get=yes`, `delete=no`.
- [ ] `prometheus.md`: gọi query metric thật qua MCP.
- [ ] Bốn screenshot Inspector có Connected, tools/list và tools/call.
- [ ] `debug-session-day2.md` hoàn thiện.
- [ ] `quiz-day2.md` hoàn thiện, đạt ít nhất 7/10.

Verifier envelope `evidence/day2.json` được tạo sau khi source/config và runtime đã ổn định. Không copy placeholder vào envelope.
