#!/usr/bin/env bash
# Native-only cross-build in the isolated local WSL toolchain, no Android Studio.
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
local_build_root="${OPENLF2_LOCAL_BUILD_ROOT:-/opt/pf-build}"
export ANDROID_HOME="${ANDROID_HOME:-/opt/android-sdk}"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
export CONAN_HOME="$local_build_root/conan"
export PATH="$local_build_root/venv/bin:$PATH"
export CMAKE_BUILD_PARALLEL_LEVEL=2
export OPENLF2_ANDROID_NATIVE_ONLY=1
mkdir -p "$CONAN_HOME"
if [[ ! -f "$CONAN_HOME/global.conf" ]]; then
    cat > "$CONAN_HOME/global.conf" <<EOF
tools.build:jobs=2
core.net.http:timeout=60
core.sources:download_cache=$project_root/engine/build/source-cache
EOF
fi
exec bash "$project_root/engine/dist/build-android.sh" "${1:-arm64-v8a}"
