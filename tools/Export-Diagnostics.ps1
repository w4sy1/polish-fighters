param([string]$ConfigDirectory=(Join-Path $PSScriptRoot '../userdata/common'))
$ErrorActionPreference='Stop'
$config=[IO.Path]::GetFullPath($ConfigDirectory)
$source=Join-Path $config 'config.json'
if (-not (Test-Path -LiteralPath $source)) { throw 'Brak ustawien gry; najpierw uruchom gre.' }
$document=Get-Content -LiteralPath $source -Raw | ConvertFrom-Json
$report=[ordered]@{}
foreach ($key in @('polish_fighters_last_crash','polish_fighters_last_session')) {
    if ($document.PSObject.Properties.Name -contains $key) { $report[$key]=$document.$key }
}
if ($report.Count -eq 0) { throw 'Brak zapisanej diagnostyki.' }
function Protect-DiagnosticValue($value) {
    if ($value -is [string]) {
        $safe=$value -replace 'https?://\S+','[URL]'
        $safe=$safe -replace '(?i)(token|password|secret|authorization)(\s*[:=]\s*)\S+','$1$2[REDACTED]'
        return ($safe -replace '(?i)Bearer\s+\S+','Bearer [REDACTED]')
    }
    if ($value -is [Collections.IDictionary]) {
        $result=[ordered]@{}
        foreach ($key in $value.Keys) { $result[$key]=Protect-DiagnosticValue $value[$key] }
        return $result
    }
    if ($value -is [pscustomobject]) {
        $result=[ordered]@{}
        foreach ($property in $value.PSObject.Properties) { $result[$property.Name]=Protect-DiagnosticValue $property.Value }
        return $result
    }
    if ($value -is [Array]) {
        [object[]]$result=@(foreach ($entry in $value) { Protect-DiagnosticValue $entry })
        return ,$result
    }
    return $value
}
$text=Protect-DiagnosticValue $report | ConvertTo-Json -Depth 16
$destination=Join-Path $config 'diagnostics'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$target=Join-Path $destination 'raport-diagnostyczny.json'
[IO.File]::WriteAllText($target,$text,[Text.UTF8Encoding]::new($false))
Write-Host "Raport lokalny: $target"
Write-Host 'Raport nie zostal wyslany. Przejrzyj go przed udostepnieniem.'
