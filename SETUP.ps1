param([ValidateSet('small','turbo')][string]$Model='small')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
New-Item -ItemType Directory -Path '.tmp','models' -Force | Out-Null
$env:TEMP=Join-Path $PSScriptRoot '.tmp'
$env:TMP=$env:TEMP
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Instale Python 3.12 de 64 bits com o Python Launcher.' }
}
$escutaPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $escutaPython -m pip install -r requirements.txt -r desktop-requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependências.' }
& $escutaPython download_model.py $Model
if ($LASTEXITCODE -ne 0) { throw 'Falha ao baixar o modelo Whisper.' }
if (-not (Test-Path -LiteralPath 'models\vosk-model-small-pt-0.3')) {
    $escutaVoskZip=Join-Path $PSScriptRoot '.tmp\vosk-model-small-pt-0.3.zip'
    Invoke-WebRequest -Uri 'https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip' -OutFile $escutaVoskZip
    Expand-Archive -LiteralPath $escutaVoskZip -DestinationPath (Join-Path $PSScriptRoot 'models') -Force
}
if ($Model -eq 'turbo') {
    & $escutaPython -c "from PySide6.QtCore import QSettings; s=QSettings('desktop-settings.ini',QSettings.Format.IniFormat); s.setValue('backend','turbo'); s.sync()"
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao configurar o motor Turbo.' }
}
Write-Host 'Instalação concluída. Abra CLAUS.cmd.'
