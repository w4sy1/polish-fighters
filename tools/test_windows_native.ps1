param([string]$TigerData)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
$vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw 'MSVC C++ Build Tools are required.' }
& (Join-Path $vs 'Common7/Tools/Launch-VsDevShell.ps1') -Arch amd64 -HostArch amd64 -SkipAutomaticLocation
$build = Join-Path $projectRoot 'engine/build/windows-tests'
$report = Join-Path $projectRoot 'validation/windows-native'
New-Item -ItemType Directory -Force -Path $build, $report | Out-Null
$flags = @('/nologo', '/std:c++latest', '/EHsc', '/W4', '/WX', '/utf-8', '/permissive-', "/I$projectRoot/engine/include")
$cases = @(
    @{ Name = 'background-layers-test'; Sources = @('tests/background_layers_test.cpp', 'engine/src/resources/background_data.cpp', 'engine/src/resources/data_file.cpp'); Args = @(); Libraries = @() },
    @{ Name = 'room-test'; Sources = @('tests/room_test.cpp', 'engine/src/engine/room.cpp'); Args = @(); Libraries = @() },
    @{ Name = 'network-compat-test'; Sources = @('tests/network_compat_test.cpp', 'engine/src/adapters/network/transport.cpp'); Args = @(); Libraries = @('/link', 'ws2_32.lib') },
    @{ Name = 'object-blocks-test'; Sources = @('tests/object_blocks_test.cpp', 'engine/src/resources/object_data.cpp', 'engine/src/resources/data_file.cpp'); Args = @(); Libraries = @() },
    @{ Name = 'package-smoke'; Sources = @('tests/package_smoke.cpp', 'engine/src/engine/packages.cpp', 'engine/src/core/files.cpp'); Args = @("$projectRoot/engine/scripts"); Libraries = @() },
    @{ Name = 'package-assets-test'; Sources = @('tests/package_assets_test.cpp', 'engine/src/engine/packages.cpp', 'engine/src/core/files.cpp'); Args = @(); Libraries = @() }
)
if ($TigerData) {
    $cases[2].Args = @((Resolve-Path -LiteralPath $TigerData).Path)
}
Push-Location $build
try {
    foreach ($case in $cases) {
        $sources = @($case.Sources | ForEach-Object { Join-Path $projectRoot $_ })
        & cl @flags @sources "/Fe:$($case.Name).exe" @($case.Libraries) 2>&1 |
            Tee-Object -FilePath (Join-Path $report "$($case.Name)-build.log")
        if ($LASTEXITCODE -ne 0) { throw "$($case.Name) compilation failed." }
        $binary = Join-Path $build "$($case.Name).exe"
        & $binary @($case.Args) 2>&1 | Tee-Object -FilePath (Join-Path $report "$($case.Name).log")
        if ($LASTEXITCODE -ne 0) { throw "$($case.Name) failed." }
    }
    $sources = @('tests/room_host_runner.cpp', 'engine/src/engine/room_host.cpp', 'engine/src/engine/room.cpp', 'engine/src/core/json.cpp', 'engine/src/adapters/network/transport.cpp') |
        ForEach-Object { Join-Path $projectRoot $_ }
    & cl @flags @sources /Fe:room-host-runner.exe /link ws2_32.lib 2>&1 |
        Tee-Object -FilePath (Join-Path $report 'room-host-build.log')
    if ($LASTEXITCODE -ne 0) { throw 'Room host compilation failed.' }
    & python (Join-Path $projectRoot 'tests/test_room_tcp.py') --runner (Join-Path $build 'room-host-runner.exe') --output (Join-Path $report 'tcp-results.json') 2>&1 |
        Tee-Object -FilePath (Join-Path $report 'tcp-test.log')
    if ($LASTEXITCODE -ne 0) { throw 'Loopback TCP tests failed.' }
} finally {
    Pop-Location
}
