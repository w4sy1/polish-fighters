"""Bundle all local game packs for sideloading; deduplicate payloads by SHA256.

The original LF2 installer is data read by the game, never executed. No userdata,
credentials, Windows DLLs or game executables are bundled. The ZIP is private/local.
"""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PACKS = ('polish-originals', 'mixed-all', 'lf4-turbo', 'dbz', 'one-piece',
         'kate', 'reinforced', 'ntsd', 'bleach')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory(root=ROOT):
    files = {}
    scripts = root / 'engine/scripts'
    for source in scripts.rglob('*'):
        if source.is_file():
            files['scripts/' + source.relative_to(scripts).as_posix()] = source
    installer = root.parent / 'downloads/LF2_v2.0a.exe'
    if sha(installer) != '540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1':
        raise ValueError('Wrong LF2 data installer')
    files['LF2_v2.0a.exe'] = installer
    for name in PACKS:
        pack = root / 'content-packs' / name
        for source in pack.iterdir():
            if source.is_file() and source.suffix in ('.lua', '.manifest', '.json', '.md'):
                files[f'content-packs/{name}/{source.name}'] = source
        for line in (pack / 'package.manifest').read_text().splitlines():
            if line.startswith('asset='):
                relative = line[6:].split('|', 1)[1]
                path = Path(relative)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('Unsafe manifest path: ' + relative)
                source = pack / path
                if not source.is_file():
                    raise FileNotFoundError(source)
                files[f'content-packs/{name}/{path.as_posix()}'] = source
    licenses = root / 'engine/build/licenses'
    if not licenses.is_dir():
        licenses = root / 'engine/out/LittleFighters-Remonoko-2026-11-06/licenses'
    for source in licenses.rglob('*'):
        if source.is_file():
            files['licenses/' + source.relative_to(licenses).as_posix()] = source
    for name in ('LICENSE', 'THIRD-PARTY-NOTICES.md'):
        files[name] = root / 'engine' / name
    return files


def bundle(files, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    records, blobs = [], {}
    for index, (name, source) in enumerate(sorted(files.items())):
        digest = sha(source)
        records.append(dict(path=name, sha256=digest, bytes=source.stat().st_size))
        blobs.setdefault(digest, source)
        if index and index % 2000 == 0:
            print(f'Hashed {index}/{len(files)} files', flush=True)
    manifest = dict(schema=1, files=records, packs=list(PACKS),
                    totalBytes=sum(r['bytes'] for r in records),
                    uniqueBytes=sum(p.stat().st_size for p in blobs.values()))
    data = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    bundle_id = hashlib.sha256(data).hexdigest()
    target = destination / 'game-bundle.zip'
    with ZipFile(target, 'w', ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('manifest.json', data)
        for index, (digest, source) in enumerate(sorted(blobs.items())):
            archive.write(source, 'blobs/' + digest)
            if index and index % 1000 == 0:
                print(f'Packed {index}/{len(blobs)} unique payloads', flush=True)
    with ZipFile(target) as check:
        if check.infolist()[0].filename != 'manifest.json':
            raise ValueError('Android requires manifest.json as the first ZIP entry')
    if target.stat().st_size >= 2_000_000_000:
        raise ValueError('Bundle exceeds single-APK size budget; do not package it')
    (destination / 'game-bundle.id').write_text(bundle_id + '\n', encoding='ascii')
    report = dict(bundle_id=bundle_id, files=len(records), unique_payloads=len(blobs),
                  logical_bytes=manifest['totalBytes'], unique_bytes=manifest['uniqueBytes'],
                  archive_bytes=target.stat().st_size, packs=list(PACKS))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=ROOT / 'engine/build/android/assets')
    args = parser.parse_args()
    report = bundle(inventory(), args.destination)
    output = ROOT / 'validation/android-apk-2026-11-06'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'bundle.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
