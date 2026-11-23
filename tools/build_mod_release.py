"""Build signed content-pack envelopes for the GitHub "mods" release and the signed catalogue.

Each release asset is a signed envelope (docs/SIGNED-MODS.md): catalog.json, catalog.sig,
manifest.json, manifest.sig and package.zip, in this order and stored without compression.
package.zip holds the installed form of one content pack: its top-level Lua, manifest, JSON
and Markdown files and every asset listed in package.manifest.

The repository catalogue mods/catalog.json lists every envelope with its release URL, size
and SHA-256 and is signed into mods/catalog.sig. The private key is read from --key and is
never copied anywhere.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'w4sy1/polish-fighters'
RELEASE_TAG = 'mods'
CATALOGUE_FORMAT = 'polish-fighters-mods'
FIXED_TIME = (2026, 1, 1, 0, 0, 0)
TOP_LEVEL = ('.lua', '.manifest', '.json', '.md')
# id: (name, profile used by the game menus, short description)
PACKS = {
    'lf4-turbo': ('LF4 Turbo', 'lf_four_turbo', 'Little Fighter 4 Turbo: postacie, etapy i dźwięki.'),
    'dbz': ('Dragon Ball Z', 'dbz', 'Mod Dragon Ball Z z własnymi trybami i muzyką.'),
    'one-piece': ('One Piece', 'one_piece', 'Postacie i etapy One Piece.'),
    'kate': ('Kate', 'kate', 'Mod Kate z odzyskanymi obiektami.'),
    'reinforced': ('Reinforced', 'reinforced', 'LF2 Reinforced.'),
    'ntsd': ('NTSD / Naruto', 'ntsd', 'Naruto: The Setting Dawn.'),
    'bleach': ('Bleach', 'bleach', 'Postacie i etapy Bleach.'),
    'polish-originals': ('Polish Fighters', 'polish_fighters', 'Oryginalne postacie Polish Fighters.'),
    'mixed-all': ('Wszystkie razem', 'all', 'Scalenie wszystkich modów w jedną grę (bardzo duża paczka).'),
}


DEFAULT_PACKS = tuple(PACKS)
for pack_id, title in (
    ('dragon-ball-super', 'Dragon Ball Super'), ('fighter-hero', 'Fighter Hero'),
    ('gf2', 'GF2'), ('lf2-ns', 'LF2 NS'), ('sx2', 'Sx2'), ('lf2-sv', 'LF2 SV'),
    ('rn-lf2', 'RN LF2'), ('lf-seed', 'LF Seed'), ('wlf2-al', 'WLF2 AL'),
    ('ce-lf2', 'CE LF2'), ('ntsd-community', 'NTSD Community'), ('ntsd-ce-setup', 'NTSD CE'),
    ('killer-lf2', 'Killer LF2'), ('oplos', 'One Piece: Legends of Sea'),
    ('mortal-kombat', 'Mortal Kombat LF2'),
):
    PACKS[pack_id] = (title, pack_id.replace('-', '_'), title)


def canonical(document):
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def sha256_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pack_files(pack):
    """Installed form of a pack, as bundled for Android (tools/prepare_android_game.py)."""
    files = {}
    for source in sorted(pack.iterdir()):
        if source.is_file() and source.suffix in TOP_LEVEL:
            files[source.name] = source
    for line in (pack / 'package.manifest').read_text(encoding='utf-8').splitlines():
        if line.startswith('asset='):
            relative = Path(line[6:].split('|', 1)[1])
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe manifest path: ' + str(relative))
            source = pack / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            files[relative.as_posix()] = source
    return files


def write_package(files, target):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        # package.manifest first lets streaming installers learn the pack ID early.
        for name in sorted(files, key=lambda item: (item != 'package.manifest', item)):
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with files[name].open('rb') as source, archive.open(info, 'w', force_zip64=True) as output:
                while chunk := source.read(1 << 20):
                    output.write(chunk)
    return sum(path.stat().st_size for path in files.values())


def stored(archive, name, data):
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build(pack_ids, output, key, version, revision, engine, packs_root=ROOT / 'content-packs'):
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for pack_id in pack_ids:
        name, profile, description = PACKS[pack_id]
        pack = packs_root / pack_id
        manifest_id = next(line[3:] for line in (pack / 'package.manifest').read_text(encoding='utf-8').splitlines()
                           if line.startswith('id='))
        if manifest_id != pack_id:
            raise ValueError(f'{pack_id}: package.manifest declares {manifest_id}')
        files = pack_files(pack)
        payload = output / f'{pack_id}.package.zip'
        unpacked = write_package(files, payload)
        asset_name = f'{pack_id}-{version}.zip'
        manifest = {
            'schema_version': 2, 'id': pack_id, 'name': name, 'version': version,
            'author': 'Autorzy modu (zgoda dla Polish Fighters)', 'license': 'Za zgodą autorów',
            'min_engine_version': engine, 'platforms': ['windows', 'android'], 'category': 'content-pack',
            'package_type': 'content-pack', 'dependencies': [], 'conflicts': [],
            'size_bytes': payload.stat().st_size, 'unpacked_size_bytes': unpacked,
            'sha256': sha256_file(payload),
            'source': {'type': 'github-release-asset',
                       'url': f'https://github.com/{REPOSITORY}/releases/download/{RELEASE_TAG}/{asset_name}'},
            'test_status': {'windows': 'pending', 'android': 'pending'}, 'required_assets': [],
            'installation': {'method': 'content-pack-zip', 'entrypoint': 'package.manifest'},
        }
        raw_manifest = canonical(manifest)
        index = canonical({'channel': 'stable', 'revision': revision,
                           'manifests': {f'{pack_id}@{version}': hashlib.sha256(raw_manifest).hexdigest()}})
        envelope = output / asset_name
        with zipfile.ZipFile(envelope, 'w', zipfile.ZIP_STORED, allowZip64=True) as archive:
            stored(archive, 'catalog.json', index)
            stored(archive, 'catalog.sig', key.sign(index))
            stored(archive, 'manifest.json', raw_manifest)
            stored(archive, 'manifest.sig', key.sign(raw_manifest))
            info = zipfile.ZipInfo('package.zip', FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            with payload.open('rb') as source, archive.open(info, 'w', force_zip64=True) as target:
                while chunk := source.read(1 << 20):
                    target.write(chunk)
        payload.unlink()
        entries.append({'id': pack_id, 'name': name, 'version': version, 'profile': profile,
                        'description': description, 'file': asset_name,
                        'url': manifest['source']['url'], 'size_bytes': envelope.stat().st_size,
                        'sha256': sha256_file(envelope), 'unpacked_size_bytes': unpacked,
                        'platforms': ['windows', 'android']})
        print(f'{asset_name}: {envelope.stat().st_size} B, {len(files)} plików', flush=True)
    return entries


def write_catalogue(entries, revision, destination, key):
    catalogue = {'format': CATALOGUE_FORMAT, 'channel': 'stable', 'revision': revision,
                 'repository': REPOSITORY, 'release': RELEASE_TAG,
                 'packages': sorted(entries, key=lambda entry: entry['id'])}
    raw = canonical(catalogue)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'catalog.json').write_bytes(raw)
    (destination / 'catalog.sig').write_bytes(key.sign(raw))
    return catalogue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key', type=Path, required=True, help='Ed25519 private key (PEM), kept outside the repository')
    parser.add_argument('--output', type=Path, default=ROOT / 'delivery/mods-release')
    parser.add_argument('--catalogue', type=Path, default=ROOT / 'mods')
    parser.add_argument('--version', default='1.0.0')
    parser.add_argument('--revision', type=int, default=1)
    parser.add_argument('--engine', default='0.1.0', help='Minimum engine version written to manifests')
    parser.add_argument('--catalogue-only', action='store_true',
                        help='Re-sign mods/catalog.json from envelopes already in --output')
    parser.add_argument('--content-packs', type=Path, default=ROOT / 'content-packs')
    parser.add_argument('packs', nargs='*', metavar='PACK', default=list(DEFAULT_PACKS))
    args = parser.parse_args()
    if unknown := set(args.packs) - PACKS.keys():
        parser.error('Unknown content pack: ' + ', '.join(sorted(unknown)))
    if ROOT in args.key.resolve().parents:
        parser.error('The private key must stay outside the repository')
    key = serialization.load_pem_private_key(args.key.read_bytes(), None)
    trusted = (ROOT / 'engine/android/app/src/main/assets/mods/catalog-ed25519.pub').read_bytes()
    if key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw) != trusted:
        parser.error('The private key does not match catalog-ed25519.pub')
    if args.catalogue_only:
        old = {entry['id']: entry for entry in json.loads((args.catalogue / 'catalog.json').read_text(encoding='utf-8'))['packages']}
        entries = []
        for pack_id in args.packs:
            envelope = args.output / f'{pack_id}-{args.version}.zip'
            if not envelope.is_file():
                continue
            entry = dict(old.get(pack_id, {}))
            name, profile, description = PACKS[pack_id]
            with zipfile.ZipFile(envelope) as archive:
                manifest = json.loads(archive.read('manifest.json'))
            entry.update({'id': pack_id, 'name': name, 'version': args.version, 'profile': profile,
                          'description': description, 'file': envelope.name, 'url': manifest['source']['url'],
                          'size_bytes': envelope.stat().st_size, 'sha256': sha256_file(envelope),
                          'unpacked_size_bytes': manifest['unpacked_size_bytes'], 'platforms': ['windows', 'android']})
            entries.append(entry)
    else:
        entries = build(args.packs, args.output, key, args.version, args.revision, args.engine, args.content_packs)
    write_catalogue(entries, args.revision, args.catalogue, key)
    print(f'Katalog: {len(entries)} paczek -> {args.catalogue}')


if __name__ == '__main__':
    main()
