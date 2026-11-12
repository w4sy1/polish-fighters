"""Apply the reviewed Android Java fixes to freshly extracted SDL 3.4.14 sources."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def apply_compat(root):
    root = Path(root).resolve()
    patch = root / 'tools/patches/sdl3-3.4.14-android.patch'
    helper = root / 'tools/patches/SDLAndroidCompat.java'
    destination = root / 'engine/build/android/sdl-java/org/libsdl/app'
    command = ['git', 'apply', '--directory=engine/build/android/sdl-java']
    check = subprocess.run(command + ['--check', str(patch)], cwd=root, capture_output=True, text=True)
    already_applied = check.returncode != 0
    if already_applied:
        reverse = subprocess.run(command + ['--reverse', '--check', str(patch)], cwd=root,
                                 capture_output=True, text=True)
        if reverse.returncode:
            raise RuntimeError('SDL source does not match the reviewed 3.4.14 patch:\n' + check.stderr)
    else:
        subprocess.run(command + [str(patch)], cwd=root, check=True)
    shutil.copy2(helper, destination / helper.name)
    return {'patch': patch.name, 'already_applied': already_applied}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    print(json.dumps(apply_compat(parser.parse_args().root)))
