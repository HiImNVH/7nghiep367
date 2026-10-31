param([string]$DataRoot=(Join-Path $PSScriptRoot '..\..\Data'), [string]$DemoRoot=(Join-Path $PSScriptRoot '..\..\Demo 2'), [string]$Clip)
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
    Push-Location -LiteralPath $DemoRoot
    try{
        & '.\.venv\Scripts\python.exe' -c "import sys;from pathlib import Path;from visign_ai.landmarks.pipeline import process_video,save_result;r=process_video(Path(sys.argv[1]));save_result(r,Path(sys.argv[2]));print(r['report']['inputStatus'],r['tensor'].shape)" $inputFile (Join-Path $out ('clip-'+[guid]::NewGuid()))
        if($LASTEXITCODE){throw 'Extraction failed'}
    }finally{Pop-Location}
}
