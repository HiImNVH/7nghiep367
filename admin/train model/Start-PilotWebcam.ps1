param(
    [Parameter(Mandatory)]
    [ValidatePattern('^[0-9a-f]{12}$')]
    [string]$JobId,
    [Alias('PilotZip')]
    [string]$PilotData,
    [ValidateSet('offline', 'online')]
    [string]$WandbMode = 'offline'
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$job = Join-Path $repo ".local/pilot-runs/$JobId"
$status = Get-Content -Raw -LiteralPath (Join-Path $job 'status.json') | ConvertFrom-Json
$artifact = Join-Path $job 'evaluated'
$model = Get-Content -Raw -LiteralPath (Join-Path $artifact 'model_info.json') | ConvertFrom-Json
if ($status.phase -ne 'complete' -or $status.id -ne $JobId -or $model.artifactKind -ne 'pilot' -or $model.modelVersion -ne "vsl-pilot-$JobId") {
    throw 'Job chưa có artifact pilot đã đánh giá.'
}
$hash = (Get-FileHash -LiteralPath (Join-Path $artifact 'model.pt') -Algorithm SHA256).Hash
if ($hash -ne $status.checkpointSha256) { throw 'Checkpoint không khớp SHA-256 của job.' }

$env:MODEL_ARTIFACT_PATH = $artifact
$env:FEATURE_SCHEMA_VERSION = $model.featureSchemaVersion
$env:WANDB_MODE = $WandbMode
if ($PilotData) { $env:VISIGN_PILOT_DATA = (Resolve-Path -LiteralPath $PilotData).Path }
if (-not $env:VISIGN_ADMIN_TOKEN) { $env:VISIGN_ADMIN_TOKEN = Read-Host 'Đặt mã admin' }

Push-Location $repo
try {
    & .\.venv-ai\Scripts\python.exe -m uvicorn visign_api.main:app --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) { throw "Backend dừng với mã $LASTEXITCODE." }
} finally {
    Pop-Location
}
