# Filesystem MCP Evidence

## Connection details

- Server: `filesystem`
- Configured package: `@modelcontextprotocol/server-filesystem@2026.8.31` (from the MCP configuration shared earlier)
- Transport: `stdio`
- Allowed root: `D:\proj\insighthub`
- Test timestamp: `2026-09-22T14:52:52Z`
- Codex version: not captured

## Tools reported by MCP

The tools reported as exposed by `filesystem` were:

```text
list_allowed_directories
directory_tree
list_directory
list_directory_with_sizes
get_file_info
read_file
read_text_file
read_multiple_files
read_media_file
search_files
create_directory
write_file
edit_file
move_file
```

For read-only verification, suitable tools include `list_allowed_directories`, `list_directory`, and `read_text_file`. The server also exposes write-capable tools (`create_directory`, `write_file`, `edit_file`, `move_file`); they were not called.

## Read-only allow-list test

### Allowed path: successful call

- Tool: `list_directory`
- Input:

```json
{"path":"D:\\proj\\insighthub"}
```

- Output:

```text
[FILE] .env
[FILE] .env.example
[DIR] .git
[DIR] .github
[FILE] .gitignore
[FILE] .mcp.json.template
[DIR] .venv
[FILE] AGENTS.md
[DIR] api
[DIR] chatops-bot
[FILE] CLAUDE.md
[FILE] docker-compose.yml
[DIR] docs
[DIR] evidence
[FILE] GETTING_STARTED.md
[DIR] infra
[DIR] ingestion-worker
[FILE] Makefile
[DIR] observability
[DIR] prometheus
[FILE] README.md
[FILE] Running-Project-Specification-Student.md
[DIR] sample-docs
[DIR] scripts
[DIR] security
[DIR] tests
[DIR] tools
[DIR] web
```

### Outside allow-list: denied

- Tool: `read_text_file`
- Input:

```json
{"path":"C:\\Windows\\win.ini"}
```

- Output:

```text
Access denied - path outside allowed directories: C:\Windows\win.ini not in D:\proj\insighthub
```

- Inspector screenshot: not captured
