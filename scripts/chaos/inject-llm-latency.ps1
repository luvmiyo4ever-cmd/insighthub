param(
    [string]$ApiUrl = "http://127.0.0.1:18000",
    [int]$Count = 12
)

$ErrorActionPreference = "Stop"
if ($Count -lt 1) { throw "Count must be positive." }

$headers = @{ "X-InsightHub-Chaos" = "llm-latency" }
$body = @{ question = "Day 4 controlled latency check" } | ConvertTo-Json
1..$Count | ForEach-Object {
    $response = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$ApiUrl/chat" `
        -Headers $headers -ContentType "application/json" -Body $body -TimeoutSec 90
    if ($response.StatusCode -ne 200) { throw "Expected HTTP 200, got $($response.StatusCode)." }
}
