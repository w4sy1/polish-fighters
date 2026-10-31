$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$vswhere=Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs=& $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
& (Join-Path $vs 'Common7/Tools/Launch-VsDevShell.ps1') -Arch x86 -HostArch amd64 -SkipAutomaticLocation
$out=Join-Path $root 'engine/build/vc80-probe'
New-Item -ItemType Directory -Force -Path $out | Out-Null
Push-Location $out
try {
 & cl /nologo /std:c++latest /EHsc /W4 /utf-8 /MT (Join-Path $root 'tests/vc80_scan_probe.cpp') /Fe:vc80-scan-probe.exe
 if ($LASTEXITCODE -ne 0) { throw 'Diagnostic build failed' }
} finally { Pop-Location }
