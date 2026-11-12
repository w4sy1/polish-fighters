"""Verify native ABIs/dependencies and the exact complete game bundle in a built APK.

Signature verification is done separately with Android SDK apksigner.
This does not claim a device execution test.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from zipfile import ZipFile
from prepare_android_game import ROOT
from verify_game_bundle import validate_bundle

SYSTEM_LIBS = {'libc.so', 'libm.so', 'libdl.so', 'liblog.so', 'libandroid.so',
               'libEGL.so', 'libGLESv1_CM.so', 'libGLESv2.so', 'libGLESv3.so',
               'libOpenSLES.so', 'libvulkan.so', 'libjnigraphics.so', 'libaaudio.so',
               'libmediandk.so', 'libz.so'}


def main(apk, output_dir=None):
    output = Path(output_dir) if output_dir else ROOT / 'validation/android-apk-2026-11-06'
    output.mkdir(parents=True, exist_ok=True)
    readelf = Path(r'C:\Users\01dwa\AppData\Local\Android\Sdk\ndk\29.0.14206865\toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-readelf.exe')
    abis = {'arm64-v8a': (2, 183), 'armeabi-v7a': (1, 40)}
    results = {}
    with ZipFile(apk) as archive:
        entries=archive.infolist()
        assert len(entries)==len({entry.filename for entry in entries}), 'duplicate APK entries'
        live_bytes=sum(entry.compress_size for entry in entries)
        overhead=Path(apk).stat().st_size-live_bytes
        assert overhead <= max(4*1024*1024,len(entries)*4096), 'incremental packaging left excessive unused bytes; clean and package again'
        manifest = archive.read('AndroidManifest.xml')
        for token in ('pl.prestigetech.polishfighters', 'GameBootstrapActivity', 'BluetoothLobbyActivity'):
            assert token.encode() in manifest or token.encode('utf-16-le') in manifest, token
        dex=b''.join(archive.read(name) for name in archive.namelist() if re.fullmatch(r'classes\d*\.dex',name))
        for token in (b'BluetoothSession;',b'StreamRelay;'):
            assert token in dex, 'missing Bluetooth implementation in DEX: '+str(token)
        for abi, (elf_class, machine) in abis.items():
            names = [n for n in archive.namelist() if n.startswith('lib/' + abi + '/') and n.endswith('.so')]
            provided = {Path(n).name for n in names}
            assert {'libmain.so', 'libSDL3.so', 'libc++_shared.so'} <= provided, abi
            checks = []
            for name in names:
                data = archive.read(name)
                assert data[:4] == b'\x7fELF' and data[4] == elf_class and data[5] == 1, name
                assert struct.unpack_from('<H', data, 18)[0] == machine, name
                if elf_class == 2:
                    phoff = struct.unpack_from('<Q', data, 32)[0]
                    stride, count = struct.unpack_from('<HH', data, 54)
                    aligns = [struct.unpack_from('<Q', data, phoff + n * stride + 48)[0]
                              for n in range(count) if struct.unpack_from('<I', data, phoff + n * stride)[0] == 1]
                    assert aligns and min(aligns) >= 16384, (name, 'ARM64 LOAD alignment below 16 KB', aligns)
                else:
                    aligns = []
                path = output / 'apk-native' / abi / Path(name).name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                dynamic = subprocess.run([str(readelf), '--dynamic', str(path)], capture_output=True, text=True, check=True).stdout
                needed = re.findall(r'\(NEEDED\).*?\[([^\]]+)\]', dynamic)
                missing = set(needed) - provided - SYSTEM_LIBS
                assert not missing, (name, missing)
                checks.append(dict(library=path.name, needed=needed, load_alignments=aligns,
                                   sha256=hashlib.sha256(data).hexdigest()))
            results[abi] = checks
        local = ROOT / 'engine/build/android/assets/game-bundle.zip'
        bundle_checks = validate_bundle(local, (local.parent / 'game-bundle.id').read_text().strip())
        source_hash = hashlib.sha256()
        with local.open('rb') as stream:
            while block := stream.read(1024 * 1024): source_hash.update(block)
        apk_hash = hashlib.sha256()
        with archive.open('assets/game-bundle.zip') as stream:
            while block := stream.read(1024 * 1024): apk_hash.update(block)
        assert source_hash.digest() == apk_hash.digest(), 'APK bundle differs from the verified local bundle'
        assert archive.read('assets/game-bundle.id') == (ROOT / 'engine/build/android/assets/game-bundle.id').read_bytes()
        assert archive.testzip() is None
    with Path(apk).open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    report = dict(pass_=True, apk=str(apk), bytes=Path(apk).stat().st_size,
                  sha256=digest, abis=results, full_game_bundle_matches=True,
                  zip_crc=True, packaging_overhead_bytes=overhead,
                  bluetooth_classes_present=True, device_tested=False, bundle_stream_contract=bundle_checks)
    (output / 'apk-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'abis'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    main(args.apk, args.output)
