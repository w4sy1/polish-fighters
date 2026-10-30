#!/usr/bin/env python3
"""Report build prerequisites; do not install or modify anything."""
import json
import os
from pathlib import Path
import shutil
import sys
sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
r={'host':sys.platform,'tools':{name:shutil.which(name) for name in ['cmake','ninja','conan','java','javac','gradle','g++','texlua']},'android_sdk':sdk,'android_ndk_r28c':bool(sdk and (Path(sdk)/'ndk/28.2.13676358/build/cmake/android.toolchain.cmake').is_file()),'windows_native_build_requires':'Windows + MSVC + Windows SDK + Inno Setup'}
print(json.dumps(r,indent=2))
