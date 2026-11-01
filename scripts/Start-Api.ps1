param([switch]$UseFixture, [string]$ArtifactPath, [string]$ClipPath, [int]$Port=8000)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv-ai\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Create .venv-ai and install AI + backend packages as documented in ai/README.md.' }
if ($UseFixture) {
    if ($ArtifactPath -or $ClipPath) { throw 'Select either -UseFixture or -ArtifactPath with -ClipPath.' }
    $artifactRoot = Join-Path $repoRoot 'services\inference-api\tests\fixtures\model-artifacts\fixture'
    Write-Host 'FIXTURE ONLY: fixed response, no MediaPipe or GRU recognition.'
} else {
    if (-not $ArtifactPath -or -not $ClipPath) { throw 'Provide -ArtifactPath and -ClipPath, or explicitly select -UseFixture.' }
    $artifactRoot = (Resolve-Path -LiteralPath $ArtifactPath).Path
    $clipFile = (Resolve-Path -LiteralPath $ClipPath).Path
}
$info = Get-Content -LiteralPath (Join-Path $artifactRoot 'model_info.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $UseFixture -and $info.artifactKind -notin @('pilot','full')) { throw 'Real inference requires a pilot/full delivery.' }
$env:MODEL_ARTIFACT_PATH = $artifactRoot
$env:FEATURE_SCHEMA_VERSION = $info.featureSchemaVersion
Push-Location -LiteralPath $repoRoot
try {
    if (-not $UseFixture) {
        & $pythonExe -m visign_api.inference.check_artifact --artifact $artifactRoot --clip $clipFile --require-delivery
        if ($LASTEXITCODE -ne 0) { throw 'Candidate failed preflight; API was not started.' }
    }
    & $pythonExe -m uvicorn visign_api.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'API exited with an error.' }
} finally { Pop-Location }
