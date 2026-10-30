param(
    [switch]$SkipDependencies,
    [string]$Installer,
    [string]$StageDirectory,
    [string[]]$PackIds = @('lf4-turbo', 'bleach', 'kate', 'reinforced', 'dbz', 'ntsd', 'one-piece')
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$engine = Join-Path $projectRoot 'engine'
$venv = Join-Path $projectRoot '.build-venv/Scripts'
if (-not (Test-Path (Join-Path $venv 'conan.exe'))) {
    throw 'Create .build-venv and install conan==2.32.0, cmake, ninja and Pillow first.'
}
if (-not $Installer) { $Installer = Join-Path $projectRoot '../downloads/LF2_v2.0a.exe' }
$Installer = (Resolve-Path -LiteralPath $Installer).Path
if ((Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash.ToLowerInvariant() -ne '540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1') {
    throw 'The supplied LF2 installer does not match the pinned LF2 v2.0a hash.'
}
$build = Join-Path $engine 'build/windows/x64'
$native = Join-Path $build 'native'
$stage = if ($StageDirectory) { [IO.Path]::GetFullPath($StageDirectory, $projectRoot) } else { Join-Path $engine 'out/PolishFighters-Windows-x64-portable' }
$report = Join-Path $projectRoot 'validation/windows-native'
New-Item -ItemType Directory -Force -Path $build, $stage, $report | Out-Null
$previousPath = $env:PATH
$previousConanHome = $env:CONAN_HOME
$env:PATH = "$venv;$env:PATH"
$env:CONAN_HOME = Join-Path $engine 'build/conan-home'
function Invoke-Logged {
    param([string]$Program, [string[]]$Arguments, [string]$Log)
    & $Program @Arguments 2>&1 | Tee-Object -FilePath (Join-Path $report $Log)
    if ($LASTEXITCODE -ne 0) { throw "$Program failed; see $Log." }
}
Push-Location $engine
try {
    if (-not $SkipDependencies) {
        if (-not (Test-Path (Join-Path $env:CONAN_HOME 'profiles/default'))) {
            Invoke-Logged conan @('profile', 'detect') 'conan-profile.log'
        }
        Invoke-Logged conan @('export', 'conan/luajit') 'conan-export.log'
        Invoke-Logged conan @('install', '.', '--profile:host', 'default', '--profile:build', 'default',
            '--output-folder', (Join-Path $build 'conan'), '--build=missing',
            '-cc', "core.sources:download_cache=$(Join-Path $engine 'build/source-cache')", '-cc', 'core.net.http:timeout=30',
            '-c', 'tools.files.download:retry=0',
            '--deployer=runtime_deploy', '--deployer-folder', (Join-Path $build 'runtime'),
            '-s:h', 'arch=x86_64', '-s:h', 'build_type=Release', '-s:h', 'compiler.cppstd=23',
            '-s:h', 'compiler.runtime=dynamic', '-s:h', 'compiler.runtime_type=Release') 'conan-install.log'
    }
    $toolchain = Join-Path $build 'conan/conan_toolchain.cmake'
    if (-not (Test-Path $toolchain)) { throw 'Conan dependencies have not been generated.' }
    Invoke-Logged cmake @('-S', $engine, '-B', $native, '-G', 'Visual Studio 17 2022', '-A', 'x64',
        "-DCMAKE_TOOLCHAIN_FILE=$toolchain", '-DOPENLF2_DEPENDENCY_PROVIDER=conan',
        "-DPython3_EXECUTABLE=$(Join-Path $venv 'python.exe')") 'cmake-configure.log'
    Invoke-Logged cmake @('--build', $native, '--config', 'Release', '--parallel', '4') 'cmake-build.log'
    Copy-Item -LiteralPath (Join-Path $native 'Release/openlf2.exe') -Destination $stage -Force
    $dlls = @(Get-ChildItem -LiteralPath (Join-Path $build 'runtime') -Recurse -File -Filter '*.dll')
    if ($dlls.Count -eq 0) { throw 'No runtime DLLs were deployed.' }
    foreach ($dll in $dlls) { Copy-Item -LiteralPath $dll.FullName -Destination $stage -Force }
    New-Item -ItemType Directory -Force -Path (Join-Path $stage 'scripts'), (Join-Path $stage 'content-packs') | Out-Null
    Copy-Item -Path (Join-Path $engine 'scripts/*') -Destination (Join-Path $stage 'scripts') -Recurse -Force
    foreach ($packId in $PackIds) {
        if ($packId -notmatch '^[a-z0-9-]+$') { throw "Invalid package ID: $packId" }
        $packSource = Join-Path $projectRoot "content-packs/$packId"
        if (-not (Test-Path -LiteralPath (Join-Path $packSource 'package.manifest'))) { throw "Missing package: $packId" }
        $packTarget = Join-Path $stage "content-packs/$packId"
        New-Item -ItemType Directory -Force -Path $packTarget | Out-Null
        Copy-Item -Path (Join-Path $packSource '*') -Destination $packTarget -Recurse -Force
    }
    Copy-Item -LiteralPath $Installer -Destination (Join-Path $stage 'LF2_v2.0a.exe') -Force
    Copy-Item -LiteralPath (Join-Path $engine 'LICENSE'), (Join-Path $engine 'THIRD-PARTY-NOTICES.md'),
        (Join-Path $projectRoot 'README_PL.md'), (Join-Path $projectRoot 'BUILD_WINDOWS.md'),
        (Join-Path $projectRoot 'PROJECT-STATUS.md') -Destination $stage -Force
    Invoke-Logged python @((Join-Path $engine 'dist/collect-licenses.py'), (Join-Path $stage 'licenses'),
        '--key', 'ffmpeg', '--key', 'ffmpeg-notes', '--key', 'sdl3', '--key', 'sdl3-ttf',
        '--key', 'freetype', '--key', 'luajit', '--key', 'zlib', '--key', 'bzip2',
        '--key', 'openssl', '--key', 'libcurl') 'licenses.log'
    foreach ($pack in (@('LF2') + $PackIds)) {
        $modArgument = if ($pack -ne 'LF2') { ' --mod "%~dp0content-packs\' + $pack + '"' } else { '' }
        $launcher = "@echo off`r`ncd /d `"%~dp0`"`r`n`"%~dp0openlf2.exe`" --installer `"%~dp0LF2_v2.0a.exe`" --scripts `"%~dp0scripts`" --mod `"%~dp0scripts\polish-fighters`" --config-dir `"%~dp0userdata\$pack`"$modArgument`r`nif errorlevel 1 pause`r`n"
        Set-Content -LiteralPath (Join-Path $stage "Graj-$pack.cmd") -Value $launcher -Encoding ascii
    }
    $files = Get-ChildItem -LiteralPath $stage -Recurse -File | ForEach-Object {
        [pscustomobject]@{ path = [IO.Path]::GetRelativePath($stage, $_.FullName); bytes = $_.Length;
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
    }
    $files | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $report 'portable-files.json') -Encoding utf8
    Write-Output "Built portable game: $stage"
} finally {
    Pop-Location
    $env:PATH = $previousPath
    $env:CONAN_HOME = $previousConanHome
}
