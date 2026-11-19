"""Validate signed managed-mod manifests and their local ZIP artifacts."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from mod_archive import inspect_zip, safe_name

ROOT = Path(__file__).resolve().parents[1]
PLAY_SUFFIXES = {'.json', '.png', '.jpg', '.jpeg', '.bmp', '.wav', '.ogg', '.mp3', '.txt', '.md'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate manifest key: {key}')
        result[key] = value
    return result


def verified_json(raw, signature, public_key):
    """Verify a detached Ed25519 signature over canonical UTF-8 JSON bytes."""
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, raw)
    except InvalidSignature as error:
        raise ValueError('Invalid manifest signature') from error

    document = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'), allow_nan=False).encode('utf-8')
    if canonical != raw:
        raise ValueError('Document must use canonical UTF-8 JSON')
    return document


def verify_manifest(raw, signature, public_key):
    manifest = verified_json(raw, signature, public_key)
    schema_path = ROOT / 'data/mods/manifest.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    try:
        Draft202012Validator(schema).validate(manifest)
    except ValidationError as error:
        field = '.'.join(map(str, error.absolute_path)) or 'manifest'
        raise ValueError(f'{field}: {error.message}') from error

    safe_name(manifest['installation']['entrypoint'])
    return manifest


def verify_catalog(raw, signature, public_key, channel, *, min_revision=1):
    catalog = verified_json(raw, signature, public_key)
    if (not isinstance(catalog, dict) or set(catalog) != {'channel', 'revision', 'manifests'}
            or channel not in ('dev', 'test', 'stable') or catalog['channel'] != channel
            or type(catalog['revision']) is not int or catalog['revision'] < min_revision
            or not isinstance(catalog['manifests'], dict)):
        raise ValueError('Invalid catalogue channel, revision or manifest index')
    for digest in catalog['manifests'].values():
        if not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            raise ValueError('Invalid catalogue manifest hash')
    return catalog


def verify_package(raw, signature, public_key, archive, *, google_play=False):
    manifest = verify_manifest(raw, signature, public_key)
    if google_play and 'android' not in manifest['platforms']:
        raise ValueError('Package does not support Android')
    with archive.open('rb') as source:
        if source.seek(0, 2) != manifest['size_bytes']:
            raise ValueError('Package size differs from manifest')
        source.seek(0)
        if hashlib.file_digest(source, 'sha256').hexdigest() != manifest['sha256']:
            raise ValueError('Package SHA-256 differs from manifest')

    report = inspect_zip(archive)
    if report['total_bytes'] != manifest['unpacked_size_bytes']:
        raise ValueError('Unpacked size differs from manifest')
    names = {entry['name'] for entry in report['files']}
    if manifest['installation']['entrypoint'] not in names:
        raise ValueError('Package entrypoint is missing')
    if google_play and any(Path(name).suffix.lower() not in PLAY_SUFFIXES for name in names):
        raise ValueError('File type is forbidden for Google Play')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('signature', type=Path, help='Raw 64-byte Ed25519 signature')
    parser.add_argument('public_key', type=Path, help='Trusted raw 32-byte Ed25519 public key')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--catalog-signature', type=Path, required=True)
    parser.add_argument('--channel', choices=('dev', 'test', 'stable'), default='stable')
    parser.add_argument('--min-revision', type=int, default=1)
    parser.add_argument('--google-play', action='store_true')
    args = parser.parse_args()
    try:
        key = args.public_key.read_bytes()
        raw = args.manifest.read_bytes()
        catalog = verify_catalog(args.catalog.read_bytes(), args.catalog_signature.read_bytes(),
                                 key, args.channel, min_revision=args.min_revision)
        manifest = verify_package(raw, args.signature.read_bytes(), key, args.archive,
                                  google_play=args.google_play)
        identity = f"{manifest['id']}@{manifest['version']}"
        if catalog['manifests'].get(identity) != hashlib.sha256(raw).hexdigest():
            raise ValueError('Manifest is not pinned in this catalogue')
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
