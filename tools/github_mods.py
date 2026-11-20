"""Signed Polish Fighters mod catalogue on GitHub: fetch, verify, download and install.

The catalogue (mods/catalog.json + mods/catalog.sig in the repository) lists signed
envelopes published as assets of the GitHub release "mods". Every step is checked against
the trusted Ed25519 key: the catalogue signature, the envelope size and SHA-256 from the
catalogue, then the signatures, pin, size and SHA-256 inside the envelope. Only then is the
content pack unpacked into <game>/content-packs/<id>, replacing an older copy atomically.
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from mod_archive import has_link_component, safe_name

ROOT = Path(__file__).resolve().parents[1]
TRUSTED_KEY = ROOT / 'engine/android/app/src/main/assets/mods/catalog-ed25519.pub'
REPOSITORY = 'w4sy1/polish-fighters'
CATALOGUE_URL = f'https://raw.githubusercontent.com/{REPOSITORY}/main/mods/catalog.json'
SIGNATURE_URL = f'https://raw.githubusercontent.com/{REPOSITORY}/main/mods/catalog.sig'
SOURCE_NAME = 'Polish Fighters — GitHub'
FORMAT = 'polish-fighters-mods'
ASSET_URL = re.compile(r'https://github\.com/w4sy1/polish-fighters/releases/download/mods/[a-z0-9-]{1,64}-[0-9.]{5,20}\.zip')
DOWNLOAD_HOSTS = {'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com'}
ID = re.compile(r'[a-z0-9]+(-[a-z0-9]+)*')
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)')
META_LIMIT = 1024 * 1024
ENVELOPE_LIMIT = 2 * 1024 * 1024 * 1024
UNPACKED_LIMIT = 4 * 1024 * 1024 * 1024
MAX_FILES = 20000
FORBIDDEN = {'.exe', '.dll', '.so', '.dylib', '.bat', '.cmd', '.ps1', '.sh', '.py', '.com', '.scr', '.msi', '.jar', '.vbs', '.js'}
ENVELOPE = ('catalog.json', 'catalog.sig', 'manifest.json', 'manifest.sig', 'package.zip')
USER_AGENT = 'PolishFighters-Mods/1'


def trusted_key(path=TRUSTED_KEY):
    key = Path(path).read_bytes()
    if len(key) != 32:
        raise ValueError('Trusted mod catalogue key must have 32 bytes')
    return key


def verify_catalogue(raw, signature, key):
    """Return the verified catalogue or raise ValueError."""
    from verify_mod_package import verified_json
    if len(raw) > META_LIMIT or len(signature) != 64:
        raise ValueError('Invalid catalogue size or signature length')
    catalogue = verified_json(raw, signature, key)
    if (not isinstance(catalogue, dict) or catalogue.get('format') != FORMAT
            or catalogue.get('channel') != 'stable' or type(catalogue.get('revision')) is not int
            or catalogue['revision'] < 1 or not isinstance(catalogue.get('packages'), list)):
        raise ValueError('Invalid mod catalogue')
    seen = set()
    for entry in catalogue['packages']:
        if (not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or not ID.fullmatch(entry['id'])
                or len(entry['id']) > 64 or entry['id'] in seen
                or not isinstance(entry.get('version'), str) or not VERSION.fullmatch(entry['version'])
                or not isinstance(entry.get('name'), str) or not 0 < len(entry['name']) <= 120
                or not isinstance(entry.get('url'), str) or not ASSET_URL.fullmatch(entry['url'])
                or not entry['url'].endswith(f"/{entry['id']}-{entry['version']}.zip")
                or type(entry.get('size_bytes')) is not int or not 0 < entry['size_bytes'] <= ENVELOPE_LIMIT
                or type(entry.get('unpacked_size_bytes')) is not int
                or not 0 < entry['unpacked_size_bytes'] <= UNPACKED_LIMIT
                or not isinstance(entry.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', entry['sha256'])):
            raise ValueError('Invalid mod catalogue entry')
        seen.add(entry['id'])
    return catalogue


def _allowed(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in DOWNLOAD_HOSTS | {'raw.githubusercontent.com'} \
            or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Download left the GitHub hosts: ' + (parsed.hostname or '?'))
    return url


class _Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        _allowed(new_url)
        return super().redirect_request(request, response, code, message, headers, new_url)


def _open(url, timeout=30):
    opener = urllib.request.build_opener(_Redirects())
    request = urllib.request.Request(_allowed(url), headers={'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'})
    return opener.open(request, timeout=timeout)


def _fetch_small(url, limit):
    with _open(url) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Response exceeds limit')
    return data


def fetch_catalogue(key=None, catalogue_url=CATALOGUE_URL, signature_url=SIGNATURE_URL):
    key = key or trusted_key()
    return verify_catalogue(_fetch_small(catalogue_url, META_LIMIT), _fetch_small(signature_url, 64), key)


def download(entry, destination, progress=None):
    """Download one envelope to `destination`, checking size and SHA-256 from the catalogue."""
    destination = Path(destination)
    partial = destination.with_name(destination.name + '.part')
    digest = hashlib.sha256()
    received = 0
    try:
        with _open(entry['url'], timeout=60) as response, partial.open('wb') as output:
            while chunk := response.read(1 << 20):
                received += len(chunk)
                if received > entry['size_bytes']:
                    raise ValueError('Download is larger than the catalogue says')
                digest.update(chunk)
                output.write(chunk)
                if progress:
                    progress(received, entry['size_bytes'])
        if received != entry['size_bytes'] or digest.hexdigest() != entry['sha256']:
            raise ValueError('Downloaded file does not match the signed catalogue')
        os.replace(partial, destination)
    finally:
        if partial.exists():
            partial.unlink()
    return destination


def _read(bundle, name, limit):
    with bundle.open(name) as source:
        data = source.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Signed metadata is too large: ' + name)
    return data


def _content_name(name):
    name = safe_name(name)
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in FORBIDDEN:
        raise ValueError('Executable files are forbidden in content packs: ' + name)
    return name


def install_envelope(envelope, packs_directory, key=None, expected_id=None, progress=None):
    """Verify a signed content-pack envelope and publish it as packs_directory/<id>."""
    from verify_mod_package import verify_catalog, verify_manifest, verify_pinned_manifest
    key = key or trusted_key()
    packs = Path(packs_directory).absolute()
    packs.mkdir(parents=True, exist_ok=True)
    if has_link_component(packs):
        raise ValueError('Content-pack directory must not be a link')
    with tempfile.TemporaryDirectory(prefix='.github-mod-', dir=packs) as temporary:
        temporary = Path(temporary)
        payload = temporary / 'package.zip'
        with zipfile.ZipFile(envelope) as bundle:
            entries = bundle.infolist()
            if [entry.filename for entry in entries] != list(ENVELOPE):
                raise ValueError('Invalid signed mod ZIP envelope')
            catalogue = verify_catalog(_read(bundle, 'catalog.json', META_LIMIT), _read(bundle, 'catalog.sig', 64), key, 'stable')
            raw = _read(bundle, 'manifest.json', META_LIMIT)
            manifest = verify_manifest(raw, _read(bundle, 'manifest.sig', 64), key)
            verify_pinned_manifest(catalogue, raw, manifest)
            if manifest['package_type'] != 'content-pack' or manifest['installation']['method'] != 'content-pack-zip':
                raise ValueError('This envelope is not a content pack')
            if expected_id and manifest['id'] != expected_id:
                raise ValueError('Envelope contains a different mod')
            if 'windows' not in manifest['platforms']:
                raise ValueError('Content pack does not support Windows')
            digest = hashlib.sha256()
            size = 0
            with bundle.open('package.zip') as source, payload.open('xb') as output:
                while chunk := source.read(1 << 20):
                    size += len(chunk)
                    if size > manifest['size_bytes']:
                        raise ValueError('Package size differs from manifest')
                    digest.update(chunk)
                    output.write(chunk)
        if size != manifest['size_bytes'] or digest.hexdigest() != manifest['sha256']:
            raise ValueError('Package SHA-256 differs from manifest')
        if shutil.disk_usage(packs).free < manifest['unpacked_size_bytes'] + 64 * 1024 * 1024:
            raise ValueError('Insufficient free disk space')
        staging = temporary / manifest['id']
        with zipfile.ZipFile(payload) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            if not infos or len(infos) > MAX_FILES:
                raise ValueError('Invalid number of content-pack files')
            names = set()
            total = 0
            for info in infos:
                name = _content_name(info.filename)
                if name.casefold() in names or info.flag_bits & 1:
                    raise ValueError('Duplicate or encrypted content-pack entry')
                names.add(name.casefold())
                total += info.file_size
                if total > manifest['unpacked_size_bytes']:
                    raise ValueError('Unpacked size differs from manifest')
            if total != manifest['unpacked_size_bytes'] or 'package.manifest' not in names:
                raise ValueError('Content pack is incomplete')
            for index, info in enumerate(infos, 1):
                target = staging / _content_name(info.filename)
                target.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with archive.open(info) as source, target.open('xb') as output:
                    while chunk := source.read(1 << 20):
                        written += len(chunk)
                        if written > info.file_size:
                            raise ValueError('ZIP entry exceeds declared size')
                        output.write(chunk)
                if written != info.file_size:
                    raise ValueError('Truncated ZIP entry')
                if progress and index % 100 == 0:
                    progress(index, len(infos))
        lines = (staging / 'package.manifest').read_text(encoding='utf-8').splitlines()
        if f"id={manifest['id']}" not in lines:
            raise ValueError('package.manifest declares a different ID')
        target = packs / manifest['id']
        backup = None
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_dir():
                raise ValueError('Content-pack path is occupied')
            backup = temporary / '.previous'
            target.rename(backup)
        try:
            staging.rename(target)
        except BaseException:
            if backup and backup.exists():
                backup.rename(target)
            raise
    return manifest


def default_packs_directory():
    """The engine reads content-packs next to the scripts directory of the installed game."""
    for candidate in (Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Polish Fighters', ROOT):
        if (candidate / 'scripts').is_dir() or (candidate / 'content-packs').is_dir():
            return candidate / 'content-packs'
    return ROOT / 'content-packs'


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    install = commands.add_parser('install')
    install.add_argument('id')
    install.add_argument('--packs', type=Path, default=None, help='Target content-packs directory')
    install.add_argument('--envelope', type=Path, help='Use an already downloaded envelope')
    args = parser.parse_args()
    try:
        if args.command == 'list':
            print(json.dumps(fetch_catalogue()['packages'], ensure_ascii=False, indent=2))
            return
        catalogue = fetch_catalogue()
        entry = next((item for item in catalogue['packages'] if item['id'] == args.id), None)
        if not entry:
            raise ValueError('Unknown mod: ' + args.id)
        packs = args.packs or default_packs_directory()
        with tempfile.TemporaryDirectory(prefix='.download-', dir=packs.parent if packs.parent.is_dir() else None) as work:
            envelope = args.envelope or download(entry, Path(work) / entry['url'].rsplit('/', 1)[1],
                                                 lambda done, total: print(f'\r{done * 100 // total}%', end='', flush=True))
            print()
            manifest = install_envelope(envelope, packs, expected_id=entry['id'])
        print(f"Zainstalowano {manifest['name']} {manifest['version']} w {packs / manifest['id']}")
    except (ValueError, OSError, zipfile.BadZipFile) as problem:
        parser.exit(1, f'{problem}\n')


if __name__ == '__main__':
    main()
