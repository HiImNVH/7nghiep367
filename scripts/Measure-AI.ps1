param(
    [Parameter(Mandatory=$true)][string[]]$ClipPaths,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [ValidateRange(1,100)][int]$Repeats=5
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $repoRoot '.venv-ai\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Install .venv-ai first; see ai/README.md.' }
$clips = @($ClipPaths | ForEach-Object { (Resolve-Path -LiteralPath $_).Path })
$outputRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
Push-Location -LiteralPath $repoRoot
try {
    Write-Host 'REAL MediaPipe preprocessing; excludes GRU, HTTP and frontend. Schema is still under review.'
    & $pythonExe -m visign_ai.evaluation.benchmark_preprocessing --clips @clips --repeats $Repeats --output $outputRoot
    if ($LASTEXITCODE -ne 0) { throw 'Preprocessing benchmark failed.' }
    Write-Host "Report: $outputRoot\benchmark.json"
} finally { Pop-Location }
