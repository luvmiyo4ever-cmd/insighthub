param(
    [ValidateSet("up", "down")]
    [string]$Action = "up",
    [string]$Namespace = "insighthub-prod",
    [string]$KubeContext = "kind-insighthub-lab"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\")).Path
$clusterName = "insighthub-lab"

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $Name"
    }
}

if ($Action -eq "down") {
    Require-Command "kind"
    & kind delete cluster --name $clusterName
    exit $LASTEXITCODE
}

Require-Command "docker"
Require-Command "kind"
Require-Command "kubectl"
Require-Command "helm"

& docker info | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Docker daemon is unavailable"
}

$existing = & kind get clusters 2>$null
if ($existing -notcontains $clusterName) {
    & kind create cluster --config (Join-Path $repoRoot "kind\insighthub.yaml") --wait 120s
    if ($LASTEXITCODE -ne 0) { throw "kind cluster creation failed" }
}

& kubectl --context $KubeContext create namespace $Namespace --dry-run=client -o yaml | & kubectl --context $KubeContext apply -f -
if ($LASTEXITCODE -ne 0) { throw "namespace setup failed" }

$passwordBytes = New-Object byte[] 24
[Security.Cryptography.RandomNumberGenerator]::Fill($passwordBytes)
$password = [Convert]::ToBase64String($passwordBytes).Replace("+", "-").Replace("/", "_").TrimEnd("=")
$encodedPassword = [Uri]::EscapeDataString($password)
$databaseUrl = "postgresql://insighthub:$encodedPassword@insighthub-postgres:5432/insighthub"
$redisUrl = "redis://insighthub-redis:6379/0"

& kubectl --context $KubeContext -n $Namespace create secret generic insighthub-runtime-secrets `
    --from-literal=DATABASE_URL=$databaseUrl `
    --from-literal=REDIS_URL=$redisUrl `
    --from-literal=POSTGRES_PASSWORD=$password `
    --dry-run=client -o yaml | & kubectl --context $KubeContext apply -f -
if ($LASTEXITCODE -ne 0) { throw "runtime secret setup failed" }

& docker build --tag insighthub/api:kind (Join-Path $repoRoot "api")
if ($LASTEXITCODE -ne 0) { throw "API image build failed" }
& docker build --tag insighthub/web:kind (Join-Path $repoRoot "web")
if ($LASTEXITCODE -ne 0) { throw "web image build failed" }

& kind load docker-image insighthub/api:kind --name $clusterName
if ($LASTEXITCODE -ne 0) { throw "API image load failed" }
& kind load docker-image insighthub/web:kind --name $clusterName
if ($LASTEXITCODE -ne 0) { throw "web image load failed" }

& helm upgrade --install insighthub (Join-Path $repoRoot "charts\insighthub") `
    --namespace $Namespace --create-namespace `
    --values (Join-Path $repoRoot "charts\insighthub\values-local.yaml") `
    --wait --wait-for-jobs --timeout 10m
if ($LASTEXITCODE -ne 0) { throw "Helm install failed" }

& kubectl --context $KubeContext -n $Namespace get pods -o wide
& kubectl --context $KubeContext -n $Namespace get svc
