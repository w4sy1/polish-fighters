$ErrorActionPreference='Stop'
$records=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
foreach($record in $records){
 $result=Join-Path $PSScriptRoot $record.output
 if(Test-Path -LiteralPath $result){if((Get-FileHash -LiteralPath $result -Algorithm SHA256).Hash -ieq $record.sha256){Write-Host "Gotowy: $result";continue};throw "Plik docelowy juz istnieje z inna zawartoscia: $result"}
 foreach($part in $record.parts){$p=Join-Path $PSScriptRoot $part.name;if(!(Test-Path -LiteralPath $p)){throw "Pobierz brakujacy plik: $($part.name)"};if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ine $part.sha256){throw "Uszkodzona czesc: $($part.name)"}}
 $stream=[IO.File]::Create($result)
 try{foreach($part in $record.parts){$inputStream=[IO.File]::OpenRead((Join-Path $PSScriptRoot $part.name));try{$inputStream.CopyTo($stream)}finally{$inputStream.Dispose()}};$stream.Flush($true)}finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $result -Algorithm SHA256).Hash -ine $record.sha256){throw "Niezgodna suma polaczonego pliku: $result"}
 Write-Host "Gotowy: $result"
}
Write-Host 'Rozpakuj PolishFighters-Windows.zip i uruchom GRAJ.cmd. APK zainstaluj na Androidzie.'
