"""Verify and stage the actual Android ZIP for native desktop content smoke tests.

This checks the full archive and logical paths, not Android Activity/device execution.
"""
import hashlib
import argparse
import json
import os
from pathlib import Path
from zipfile import ZipFile
from prepare_android_game import ROOT, PACKS
from verify_game_bundle import validate_bundle


def main(output_dir=None):
    assets = ROOT / 'engine/build/android/assets'
    output = Path(output_dir) if output_dir else ROOT / 'validation/android-apk-2026-11-06'
    validate_bundle(assets / 'game-bundle.zip', (assets / 'game-bundle.id').read_text().strip())
    target = output / 'unpacked-game'
    blobs = target / '.blobs'
    blobs.mkdir(parents=True, exist_ok=True)
    with ZipFile(assets / 'game-bundle.zip') as archive:
        manifest_bytes = archive.read('manifest.json')
        assert hashlib.sha256(manifest_bytes).hexdigest() == (assets / 'game-bundle.id').read_text().strip()
        manifest = json.loads(manifest_bytes)
        assert manifest['schema'] == 1 and manifest['packs'] == list(PACKS)
        counts, hashes = {}, set()
        for item in manifest['files']:
            path = Path(item['path'])
            assert not path.is_absolute() and '..' not in path.parts
            digest = item['sha256']
            assert len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
            counts[digest] = item['bytes']
        for index, (digest, size) in enumerate(counts.items()):
            blob = blobs / digest
            hasher = hashlib.sha256()
            count = 0
            with archive.open('blobs/' + digest) as source, blob.open('wb') as dest:
                while data := source.read(1024 * 1024):
                    dest.write(data)
                    hasher.update(data)
                    count += len(data)
            assert count == size and hasher.hexdigest() == digest, digest
            hashes.add(digest)
            if index and index % 2000 == 0:
                print('Verified payloads', index, flush=True)
        for item in manifest['files']:
            path = target / item['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                # This is only the generated validation tree, never source/userdata.
                assert path.resolve().is_relative_to(target.resolve())
                path.unlink()
            os.link(blobs / item['sha256'], path)
        assert set(archive.namelist()) == {'manifest.json'} | {'blobs/' + sha for sha in hashes}
    for pack in PACKS:
        root = target / 'content-packs' / pack
        assert (root / 'package.manifest').is_file()
        for line in (root / 'package.manifest').read_text().splitlines():
            if line.startswith('asset='):
                assert (root / line[6:].split('|', 1)[1]).is_file(), line
    assert (target / 'content-packs/polish-originals/remonoko.lua').is_file()
    report = dict(pass_=True, files=len(manifest['files']), verified_payloads=len(hashes),
                  packs=list(PACKS), sha256_verified=True, native_content_root=str(target))
    (output / 'bundle-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    main(parser.parse_args().output)
