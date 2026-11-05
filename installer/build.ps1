param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$Compiler
)
$ErrorActionPreference='Stop'
$clausRepo=Split-Path -Parent $PSScriptRoot
$clausSource=(Resolve-Path -LiteralPath $SourceRoot).Path
$clausCompiler=(Resolve-Path -LiteralPath $Compiler).Path
$clausStage=Join-Path $clausRepo '.release-staging\payload'
$clausApp=Join-Path $clausStage 'transcritor-local'
$clausOutput=Join-Path $clausRepo 'releases'
New-Item -ItemType Directory -Path $clausApp,$clausOutput -Force | Out-Null

function Copy-ClausTree([string]$Source,[string]$Destination) {
    & robocopy $Source $Destination /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD __pycache__ .git qml include /XF '*.pyc' '*.log' '*.obj' '*.pdb' | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "Falha ao copiar $Source" }
}

$clausLauncher=Join-Path (Split-Path -Parent $clausSource) 'Claus.exe'
Copy-Item -LiteralPath $clausLauncher -Destination $clausStage
Get-ChildItem -LiteralPath $clausSource -File | Where-Object {
    $_.Extension -eq '.py' -and $_.Name -notmatch '^(test_|benchmark_|integration_check|voice_smoke|import_wave|brand_assets)'
} | Copy-Item -Destination $clausApp
@('requirements.txt','desktop-requirements.txt','DESKTOP.md') | ForEach-Object {
    Copy-Item -LiteralPath (Join-Path $clausSource $_) -Destination $clausApp
}
Copy-Item -LiteralPath (Join-Path $clausRepo 'THIRD_PARTY.md') -Destination $clausApp
foreach($clausFolder in @('assets','static','.python','runtime')) {
    Copy-ClausTree (Join-Path $clausSource $clausFolder) (Join-Path $clausApp $clausFolder)
}
Copy-ClausTree (Join-Path $clausSource '.venv\Lib') (Join-Path $clausApp '.venv\Lib')
New-Item -ItemType Directory -Path (Join-Path $clausApp '.venv\Scripts') -Force | Out-Null
@('python.exe','pythonw.exe') | ForEach-Object {
    Copy-Item -LiteralPath (Join-Path $clausSource ('.venv\Scripts\'+$_)) -Destination (Join-Path $clausApp '.venv\Scripts')
}
foreach($clausModel in @('small','ggml','vosk-model-small-pt-0.3')) {
    Copy-ClausTree (Join-Path $clausSource ('models\'+$clausModel)) (Join-Path $clausApp ('models\'+$clausModel))
}
& $clausCompiler /Q ('/DPayloadDir='+$clausStage) ('/DReleaseDir='+$clausOutput) (Join-Path $PSScriptRoot 'Claus.iss')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar o instalador.' }
Get-ChildItem -LiteralPath $clausOutput -Filter '*.exe' | ForEach-Object {
    $clausHash=Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    ($clausHash.Hash.ToLower()+'  '+$_.Name) | Set-Content -LiteralPath ($_.FullName+'.sha256') -Encoding ascii
    [PSCustomObject]@{Installer=$_.Name;MiB=[math]::Round($_.Length/1MB,1);SHA256=$clausHash.Hash}
}
