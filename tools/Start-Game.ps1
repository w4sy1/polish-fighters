param([switch]$Clean,[string]$InputTrace,[string]$ConfigurationDirectory)
$ErrorActionPreference='Continue'
$gameRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$configRoot=if ($ConfigurationDirectory) { [IO.Path]::GetFullPath($ConfigurationDirectory) } else { Join-Path $gameRoot 'userdata/common' }
$logs=Join-Path $configRoot 'diagnostics'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$latest=Join-Path $logs 'session-latest.log'
$previous=Join-Path $logs 'session-previous.log'
if (Test-Path -LiteralPath $latest) { Move-Item -LiteralPath $latest -Destination $previous -Force }
$writer=[IO.StreamWriter]::new($latest,$false,[Text.UTF8Encoding]::new($false))
$arguments=@('--installer',(Join-Path $gameRoot 'LF2_v2.0a.exe'),'--scripts',(Join-Path $gameRoot 'scripts'),'--config-dir',$configRoot)
if ($Clean) { $arguments+='--legacy-menu' }
if ($InputTrace) { $arguments+=@('--input-trace',$InputTrace) }
Push-Location -LiteralPath $gameRoot
try {
    & (Join-Path $gameRoot 'LittleFighters.exe') @arguments 2>&1 | ForEach-Object {
        if ($writer.BaseStream.Position -gt 1048576) {
            $writer.Dispose()
            Move-Item -LiteralPath $latest -Destination $previous -Force
            $writer=[IO.StreamWriter]::new($latest,$false,[Text.UTF8Encoding]::new($false))
        }
        $line=([string]$_) -replace 'https?://\S+','[URL]'
        $line=$line -replace '(?i)(token|password|secret|authorization)(\s*[:=]\s*)\S+','$1$2[REDACTED]'
        $line=$line -replace '(?i)Bearer\s+\S+','Bearer [REDACTED]'
        $writer.WriteLine($line);$writer.Flush()
    }
    $gameExit=$LASTEXITCODE
} finally { $writer.Dispose();Pop-Location }
if ($gameExit -ne 0) { Write-Host "Gra zakonczyla sie bledem. Raporty: $logs" }
exit $gameExit
