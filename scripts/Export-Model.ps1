param(
    [Parameter(Mandatory=$true)][string]$ArtifactPath,
    [Parameter(Mandatory=$true)][string]$ClipPath,
    [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv-ai\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Install .venv-ai first; see ai/README.md.' }
$artifactRoot = (Resolve-Path -LiteralPath $ArtifactPath).Path
$clipFile = (Resolve-Path -LiteralPath $ClipPath).Path
$deliveryPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
$info = Get-Content -LiteralPath (Join-Path $artifactRoot 'model_info.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$env:FEATURE_SCHEMA_VERSION = $info.featureSchemaVersion
Push-Location -LiteralPath $repoRoot
try {
    & $pythonExe -m visign_api.inference.package_artifact --artifact $artifactRoot --clip $clipFile --output $deliveryPath
    if ($LASTEXITCODE -ne 0) { throw 'Export failed. No incomplete delivery was published.' }
} finally { Pop-Location }
