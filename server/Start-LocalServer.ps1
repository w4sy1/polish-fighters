param(
    [ValidateRange(1024,65535)][int]$Port = 8765,
    [string]$Python = 'python',
    [string]$DataDirectory = (Join-Path $PSScriptRoot '..\userdata\server')
)
$ErrorActionPreference = 'Stop'
$serverData = [IO.Path]::GetFullPath($DataDirectory)
New-Item -ItemType Directory -Force -Path $serverData | Out-Null
$serviceScript = Join-Path $PSScriptRoot '..\tools\account_service.py'
Write-Host "Konta i katalog pokoi: http://127.0.0.1:$Port"
Write-Host "Baza: $(Join-Path $serverData 'accounts.sqlite'). Zatrzymanie: Ctrl+C."
& $Python $serviceScript --database (Join-Path $serverData 'accounts.sqlite') --port $Port
if ($LASTEXITCODE -ne 0) { throw "Serwer zakonczyl prace z kodem $LASTEXITCODE" }
