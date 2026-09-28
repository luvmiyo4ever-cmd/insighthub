param(
    [string]$ApiUrl = "http://127.0.0.1:18000",
    [int]$DurationMinutes = 65,
    [int]$IntervalSeconds = 10
)

$ErrorActionPreference = "Stop"
if ($DurationMinutes -lt 60) { throw "DurationMinutes must be at least 60." }
if ($IntervalSeconds -lt 1) { throw "IntervalSeconds must be positive." }

$deadline = (Get-Date).AddMinutes($DurationMinutes)
$body = @{ question = "Day 4 baseline warm-up request" } | ConvertTo-Json
while ((Get-Date) -lt $deadline) {
    $response = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$ApiUrl/chat" `
        -ContentType "application/json" -Body $body -TimeoutSec 30
    if ($response.StatusCode -ne 200) { throw "Expected HTTP 200, got $($response.StatusCode)." }
    Start-Sleep -Seconds $IntervalSeconds
}
