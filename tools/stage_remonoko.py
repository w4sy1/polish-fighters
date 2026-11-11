"""Stage a dated Windows build; hardlink only immutable imported resource payloads.

Scripts, binaries, manifests, catalogs and own character assets are independent copies.
This avoids another 3.5 GB of duplicate mod images on a nearly full drive.
"""
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'engine/out/LittleFighters-Remonoko-2026-11-06'
SOURCE = ROOT / 'engine/out/LittleFighters-mixed-online-2026-10-31'


def stage(binary=None):
    if STAGE.exists():
        raise FileExistsError('Keep older deliveries; choose a new stage name: ' + str(STAGE))
    linked = copied = 0
    for src in SOURCE.rglob('*'):
        rel = src.relative_to(SOURCE)
        if any(part in ('userdata', 'recordings', 'recording', 'server', 'tools') for part in rel.parts):
            continue
        if not src.is_file():
            continue
        dst = STAGE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        immutable = (len(rel.parts) > 3 and rel.parts[0] == 'content-packs'
                     and rel.parts[1] != 'polish-originals' and 'assets' in rel.parts
                     and src.suffix.lower() != '.txt')
        if immutable:
            os.link(src, dst)
            linked += 1
        else:
            shutil.copy2(src, dst)
            copied += 1
    for name in ('LittleFighters.exe', 'openlf2.exe'):
        shutil.copy2(binary or ROOT / 'engine/build/windows/x64/native/Release/openlf2.exe', STAGE / name)
    shutil.copytree(ROOT / 'engine/scripts', STAGE / 'scripts', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'content-packs/polish-originals', STAGE / 'content-packs/polish-originals', dirs_exist_ok=True)
    # The generated mixed catalog adds the five new records; other mixed payloads remain immutable.
    shutil.copy2(ROOT / 'content-packs/mixed-all/catalog.lua', STAGE / 'content-packs/mixed-all/catalog.lua')
    shutil.copy2(ROOT / 'content-packs/mixed-all/assets/catalog.txt', STAGE / 'content-packs/mixed-all/assets/catalog.txt')
    for filename, mods in (
        ('Graj-Remonoko.cmd', ['polish-originals']),
        ('Graj-Wszystkie-Mody.cmd', ['polish-originals', 'mixed-all']),
    ):
        args = ' '.join('--mod "%~dp0content-packs/' + mod + '"' for mod in mods)
        command = ('@echo off\r\ncd /d "%~dp0"\r\n'
                   '"%~dp0LittleFighters.exe" --installer "%~dp0LF2_v2.0a.exe" '
                   '--scripts "%~dp0scripts" --mod "%~dp0scripts/polish-fighters" ' + args +
                   ' --config-dir "%~dp0userdata/common"\r\nif errorlevel 1 pause\r\n')
        (STAGE / filename).write_bytes(command.encode('ascii'))
    print(f'{STAGE}\nCopied {copied} files; linked {linked} immutable resource files; no old userdata copied')


if __name__ == '__main__':
    stage()
