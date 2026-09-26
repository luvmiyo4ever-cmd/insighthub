param(
    [string]$Namespace = "insighthub-prod",
    [string]$KubeContext = "kind-insighthub-lab",
    [int]$ApiPort = 18000,
    [int]$WebPort = 13000
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$apiForward = $null
$webForward = $null

try {
    $apiForward = Start-Process kubectl -ArgumentList @("--context", $KubeContext, "-n", $Namespace, "port-forward", "svc/insighthub-api", "$ApiPort`:8000") -PassThru -WindowStyle Hidden
    $webForward = Start-Process kubectl -ArgumentList @("--context", $KubeContext, "-n", $Namespace, "port-forward", "svc/insighthub-web", "$WebPort`:3000") -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3

    $env:API_URL = "http://127.0.0.1:$ApiPort"
    $env:WEB_URL = "http://127.0.0.1:$WebPort"
    & python (Join-Path $repoRoot "scripts\kind_smoke.py")
    if ($LASTEXITCODE -ne 0) { throw "kind smoke failed" }

    Write-Host "UI is available at http://127.0.0.1:$WebPort for Microsoft Edge verification."
}
finally {
    if ($apiForward -and -not $apiForward.HasExited) { Stop-Process -Id $apiForward.Id -Force }
    if ($webForward -and -not $webForward.HasExited) { Stop-Process -Id $webForward.Id -Force }
}
