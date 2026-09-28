param(
    [string]$ApiUrl = "http://127.0.0.1:18000",
    [string]$Sample = "sample-docs/so-tay-van-hanh.md",
    [int]$Count = 20
)

$ErrorActionPreference = "Stop"
if ($Count -lt 1) { throw "Count must be positive." }
if (-not (Test-Path -LiteralPath $Sample)) { throw "Sample file not found: $Sample" }

# Configure the operator-only worker delay first (see README). Keep the worker
# available: it owns the queue-depth metric scraped by Prometheus.
1..$Count | ForEach-Object {
    $status = curl.exe -sS -o NUL -w "%{http_code}" -X POST "$ApiUrl/documents" -F "file=@$Sample"
    if ($status -ne "202") { throw "Expected HTTP 202, got $status." }
}
