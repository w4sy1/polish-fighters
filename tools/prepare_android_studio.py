"""Stage genuine pinned SDL Java, own scripts and generated icons for Android Studio.
Native ARM libraries are built separately by engine/dist/build-android.sh.
"""
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SDL_URL='https://github.com/libsdl-org/SDL/releases/download/release-3.4.14/SDL3-3.4.14.tar.gz'
SDL_SHA='30d4aa2b3037718142b32dffd4e72f917ebb6cc5227150e7bb9c45efb2153aeb'

def prepare(root=ROOT):
    root=Path(root);engine=root/'engine';stage=engine/'build/android'
    stage.mkdir(parents=True,exist_ok=True)
    archive=stage/'SDL3-3.4.14.tar.gz'
    if not archive.exists():
        with urllib.request.urlopen(SDL_URL,timeout=60) as response:blob=response.read(32*1024*1024)
        if hashlib.sha256(blob).hexdigest()!=SDL_SHA:raise ValueError('SDL source hash mismatch')
        archive.write_bytes(blob)
    blob=archive.read_bytes()
    if hashlib.sha256(blob).hexdigest()!=SDL_SHA:raise ValueError('SDL cache hash mismatch')
    prefix='SDL3-3.4.14/android-project/app/src/main/java/'
    count=0
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.startswith(prefix+'org/libsdl/app/') or not member.name.endswith('.java'):continue
            relative=Path(member.name[len(prefix):])
            if '..' in relative.parts or relative.is_absolute():raise ValueError('Unsafe SDL member')
            target=stage/'sdl-java'/relative;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(tar.extractfile(member).read());count+=1
    if count<5:raise ValueError('SDL Java source missing')
    # Reapplied to freshly extracted, hash-verified sources on every build.
    subprocess.run([sys.executable, str(root/'tools/apply_sdl_android_compat.py'), '--root', str(root)], check=True)
    subprocess.run([sys.executable,str(engine/'tools/icons/make_icons.py'),str(stage/'icons')],check=True)
    shutil.copytree(stage/'icons/android/res',stage/'res',dirs_exist_ok=True)
    shutil.copytree(engine/'scripts',stage/'assets/scripts',dirs_exist_ok=True)
    proof={'sdl_source':SDL_URL,'sdl_sha256':SDL_SHA,'java_files':count+1,'android_compat_patch':'sdl3-3.4.14-android.patch',
           'native_arm64_library_present':(stage/'jniLibs/arm64-v8a/libmain.so').is_file(),
           'scope':'Java/resources and own Lua source preparation, not native Android runtime verification'}
    (stage/'studio-preparation.json').write_text(json.dumps(proof,indent=2)+'\n')
    return proof
if __name__=='__main__':print(json.dumps(prepare(),indent=2))
