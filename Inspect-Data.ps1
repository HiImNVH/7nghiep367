param([string]$DataRoot=(Join-Path $PSScriptRoot '..\..\Data'), [string]$Clip)
$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath $DataRoot).Path
$out=New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot '.local')
$rows=foreach($f in Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.mp4'){
    [pscustomobject]@{file=$f.FullName.Substring($root.Length+1);sourceFolder=$f.Directory.Name;sha256=(Get-FileHash -LiteralPath $f.FullName).Hash;classLabel='';meaningId='';signerId='';split='';review='pending'}
}
$rows | Export-Csv -LiteralPath (Join-Path $out 'inventory-generated.csv') -NoTypeInformation -Encoding UTF8
Write-Output ("Inventoried {0} clips; copy inventory-generated.csv before annotating." -f @($rows).Count)
if($Clip){
    $inputFile=(Resolve-Path -LiteralPath (Join-Path $root $Clip)).Path
    if(!$inputFile.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Clip outside Data'}
    & (Join-Path $PSScriptRoot '.venv-ai\Scripts\python.exe') -m visign_ai.landmarks.inspect_clip --clip $inputFile --output (Join-Path $out ('clip-'+[guid]::NewGuid()))
    if($LASTEXITCODE){throw 'Extraction failed'}
}
