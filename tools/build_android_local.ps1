param(
    [string]$Distro = 'PolishFighters-Build',
    [string[]]$Abis = @('arm64-v8a', 'armeabi-v7a'),
    [switch]$SkipNative,
    [switch]$SkipBundle,
    [int]$VersionCode = 11,
    [string]$VersionName = '0.11.0-local',
    [string]$ApkName = 'PolishFighters-Android-LOCAL-0.11.apk'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.build-venv/Scripts/python.exe'
if (-not $SkipBundle) {
    & $python (Join-Path $PSScriptRoot 'prepare_android_game.py')
    if ($LASTEXITCODE -ne 0) { throw 'Preparing the complete local game bundle failed.' }
}
if (-not (Test-Path (Join-Path $projectRoot 'engine/build/android/assets/game-bundle.id'))) {
    throw 'The local mod bundle is missing.'
}
if (-not $SkipNative) {
    $linuxRoot = (& wsl.exe -d $Distro -u root -- wslpath -a $projectRoot).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Cannot locate the project in WSL.' }
    foreach ($abi in $Abis) {
        if ($abi -notin @('arm64-v8a', 'armeabi-v7a')) { throw "Unsupported test ABI: $abi" }
        & wsl.exe -d $Distro -u root -- bash "$linuxRoot/tools/build_android_native_wsl.sh" $abi
        if ($LASTEXITCODE -ne 0) { throw "Native Android build failed: $abi" }
    }
}
foreach ($abi in $Abis) {
    foreach ($library in @('libmain.so', 'libSDL3.so', 'libc++_shared.so')) {
        if (-not (Test-Path (Join-Path $projectRoot "engine/build/android/jniLibs/$abi/$library"))) {
            throw "Missing requested Android library: $abi/$library"
        }
    }
}
$previousJava = $env:JAVA_HOME
try {
    $env:JAVA_HOME = Join-Path $projectRoot 'engine/build/studio-jdk17/jdk-17.0.18+8'
    $sdkRoot = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android/Sdk' }
    $installedNdk = Get-ChildItem -LiteralPath (Join-Path $sdkRoot 'ndk') -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName 'toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe') } |
        Sort-Object { [version]$_.Name } -Descending | Select-Object -First 1
    $gradleArguments = @('-p', (Join-Path $projectRoot 'engine/android'), '--no-daemon', '--max-workers=2',
        '-Dorg.gradle.jvmargs=-Xmx1536m -XX:MaxMetaspaceSize=512m',
        "-Popenlf2VersionCode=$VersionCode", "-Popenlf2VersionName=$VersionName", ':app:clean', ':app:assembleDebug', ':app:testDebugUnitTest')
    if ($installedNdk) { $gradleArguments += "-Popenlf2NdkVersion=$($installedNdk.Name)" }
    & (Join-Path $projectRoot 'engine/android/gradlew.bat') @gradleArguments
    if ($LASTEXITCODE -ne 0) { throw 'APK packaging failed.' }
    $apk = Join-Path $projectRoot 'engine/out' $ApkName
    Copy-Item -LiteralPath (Join-Path $projectRoot 'engine/android/app/build/outputs/apk/debug/app-debug.apk') -Destination $apk
    Write-Output "Built APK: $apk"
    Get-FileHash -LiteralPath $apk -Algorithm SHA256
} finally {
    $env:JAVA_HOME = $previousJava
}
