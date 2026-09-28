param(
    [string]$ApiUrl = "http://127.0.0.1:18000",
    [int]$Count = 24
)

$ErrorActionPreference = "Stop"
if ($Count -lt 1) { throw "Count must be positive." }

$headers = @{ "X-InsightHub-Chaos" = "http-error" }
$body = @{ question = "Day 4 controlled error check" } | ConvertTo-Json
1..$Count | ForEach-Object {
    try {
        Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$ApiUrl/chat" `
            -Headers $headers -ContentType "application/json" -Body $body -TimeoutSec 30 | Out-Null
        throw "Expected the controlled endpoint to return HTTP 503."
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -ne 503) { throw }
    }
}
