param([string]$CompilerRoot, [switch]$SkipDependencies)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $CompilerRoot) { $CompilerRoot = Join-Path $projectRoot 'engine/build/portable-msvc' }
$toolset = Get-ChildItem -LiteralPath (Join-Path $CompilerRoot 'VC/Tools/MSVC') -Directory | Select-Object -First 1
$sdkVersion = Get-ChildItem -LiteralPath (Join-Path $CompilerRoot 'Windows Kits/10/Include') -Directory | Select-Object -First 1
if (-not $toolset -or -not $sdkVersion) { throw 'Portable C++ compiler and Windows SDK are missing.' }
$sdk = Join-Path $CompilerRoot 'Windows Kits/10'
$env:VSCMD_ARG_HOST_ARCH = 'x64'; $env:VSCMD_ARG_TGT_ARCH = 'x64'
$env:VCToolsVersion = $toolset.Name; $env:WindowsSDKVersion = "$($sdkVersion.Name)\"
$env:VCToolsInstallDir = "$($toolset.FullName)\"
$env:PATH = "$(Join-Path $projectRoot '.build-venv/Scripts');$(Join-Path $toolset.FullName 'bin/Hostx64/x64');$(Join-Path $sdk "bin/$($sdkVersion.Name)/x64");$env:PATH"
$env:INCLUDE = @((Join-Path $toolset.FullName 'include'), (Join-Path $sdk "Include/$($sdkVersion.Name)/ucrt"),
    (Join-Path $sdk "Include/$($sdkVersion.Name)/shared"), (Join-Path $sdk "Include/$($sdkVersion.Name)/um"),
    (Join-Path $sdk "Include/$($sdkVersion.Name)/winrt")) -join ';'
$env:LIB = @((Join-Path $toolset.FullName 'lib/x64'), (Join-Path $sdk "Lib/$($sdkVersion.Name)/ucrt/x64"),
    (Join-Path $sdk "Lib/$($sdkVersion.Name)/um/x64")) -join ';'
$env:CONAN_HOME = Join-Path $projectRoot 'engine/build/conan-home'
$conan = Join-Path $projectRoot 'engine/build/windows/x64/conan-portable'
if (-not $SkipDependencies) {
    & conan install (Join-Path $projectRoot 'engine') --profile:host default --profile:build default `
        --output-folder $conan --build=never '-s:h' arch=x86_64 '-s:h' build_type=Release '-s:h' compiler.cppstd=23 `
        '-s:h' compiler.runtime=dynamic '-s:h' compiler.runtime_type=Release `
        '-c:h' tools.cmake.cmaketoolchain:generator=Ninja '-c:b' tools.cmake.cmaketoolchain:generator=Ninja `
        '-c' "tools.microsoft.msbuild:installation_path=$CompilerRoot"
    if ($LASTEXITCODE -ne 0) { throw 'Portable dependency configuration failed.' }
}
$native = Join-Path $projectRoot 'engine/build/windows/x64/portable-native'
& cmake -S (Join-Path $projectRoot 'engine') -B $native -G Ninja '-DCMAKE_BUILD_TYPE=Release' `
    "-DCMAKE_TOOLCHAIN_FILE=$conan/conan_toolchain.cmake" '-DOPENLF2_DEPENDENCY_PROVIDER=conan' `
    "-DPython3_EXECUTABLE=$(Join-Path $projectRoot '.build-venv/Scripts/python.exe')"
if ($LASTEXITCODE -ne 0) { throw 'Portable Windows CMake configuration failed.' }
& cmake --build $native --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Portable Windows compilation failed.' }
Write-Output "Built: $native/openlf2.exe"
