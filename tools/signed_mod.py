"""Install a signed, declarative LF2 module without importing code from the ZIP."""
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

from mod_archive import extract_zip

ROOT = Path(__file__).resolve().parents[1]
TRUSTED_KEY = ROOT / 'engine/android/app/src/main/assets/mods/catalog-ed25519.pub'
ENVELOPE = ('catalog.json', 'catalog.sig', 'manifest.json', 'manifest.sig', 'package.zip')
META_LIMIT = 1024 * 1024
PACKAGE_LIMIT = 256 * 1024 * 1024
ASSET = re.compile(r'assets/a/[a-z0-9]{1,40}\.(?:txt|dat|bmp|png|jpg|jpeg|wav|ogg|mp3|json)')
SOUNDS = (
    'return function(base)\n local paths={\n }\n'
    ' for k,v in pairs(base.fixed_files) do base.fixed_files[k]=paths[v] or v end\n'
    ' for k,v in pairs(base.menu) do base.menu[k]=paths[v] or v end\n return base\nend\n'
)


def is_signed(archive):
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        return bool(entries and entries[0].filename == ENVELOPE[0])


def read_metadata(bundle, name, limit):
    with bundle.open(name) as source:
        raw = source.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f'Signed mod metadata is too large: {name}')
    return raw


def prepare(archive, destination, *, key_path=TRUSTED_KEY):
    from verify_mod_package import unique_object, verify_catalog, verify_package, verify_pinned_manifest

    if not key_path.is_file():
        raise ValueError('Trusted mod catalogue public key is missing')
    key = key_path.read_bytes()
    with tempfile.TemporaryDirectory(prefix='.signed-mod-', dir=destination.parent) as temporary:
        temporary = Path(temporary)
        payload = temporary / 'package.zip'
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            if [entry.filename for entry in entries] != list(ENVELOPE):
                raise ValueError('Invalid signed mod ZIP envelope')
            index = read_metadata(bundle, 'catalog.json', META_LIMIT)
            index_signature = read_metadata(bundle, 'catalog.sig', 64)
            raw = read_metadata(bundle, 'manifest.json', META_LIMIT)
            signature = read_metadata(bundle, 'manifest.sig', 64)
            catalogue = verify_catalog(index, index_signature, key, 'stable')
            if entries[-1].file_size > PACKAGE_LIMIT:
                raise ValueError('Signed package exceeds size limit')
            with bundle.open(entries[-1]) as source, payload.open('xb') as output:
                remaining = PACKAGE_LIMIT
                while chunk := source.read(65536):
                    remaining -= len(chunk)
                    if remaining < 0:
                        raise ValueError('Signed package exceeds size limit')
                    output.write(chunk)
        manifest = verify_package(raw, signature, key, payload)
        verify_pinned_manifest(catalogue, raw, manifest)
        if '-' in manifest['version']:
            raise ValueError('STABLE does not accept prerelease versions')
        if 'windows' not in manifest['platforms']:
            raise ValueError('Signed package does not support Windows')
        if any(manifest[field] for field in ('dependencies', 'conflicts', 'required_assets')):
            raise ValueError('This installer requires a self-contained signed package')
        version = re.search(r'project\(OpenLF2 VERSION ([0-9.]+)',
                            (ROOT / 'engine/CMakeLists.txt').read_text(encoding='utf-8'))[1]
        minimum = manifest['min_engine_version']
        if '-' in minimum or tuple(map(int, minimum.split('.'))) > tuple(map(int, version.split('.'))):
            raise ValueError('Signed package requires a newer engine')
        entrypoint = manifest['installation']['entrypoint']
        with zipfile.ZipFile(payload) as bundle:
            entries = bundle.infolist()
            if any(info.is_dir() or info.file_size > PACKAGE_LIMIT
                   or info.file_size > max(1, info.compress_size) * 100 for info in entries):
                raise ValueError('Signed module exceeds ZIP entry limits')
            files = sorted(info.filename for info in entries)
            assets = [name for name in files if name != entrypoint]
            if (entrypoint != 'module.json' or not assets or len(assets) > 4096
                    or any(not ASSET.fullmatch(name) for name in assets)):
                raise ValueError('Invalid signed module layout')
            recipe = json.loads(read_metadata(bundle, entrypoint, META_LIMIT), object_pairs_hook=unique_object)
        if (not isinstance(recipe, dict) or set(recipe) != {'source', 'stage'}
                or not isinstance(recipe['source'], str) or not isinstance(recipe['stage'], str)
                or recipe['source'] not in assets or not recipe['source'].endswith('.txt')
                or recipe['stage'] not in assets or not recipe['stage'].endswith('.dat')):
            raise ValueError('Invalid signed module recipe')

        pack_id = 'mod-' + hashlib.sha256(
            ('signed:' + manifest['id']).encode('ascii')).hexdigest()[:24]
        prefix = f'mods/{pack_id}/'
        extract_zip(payload, destination)
        (destination / entrypoint).unlink()
        adapters = {
            'package.manifest': (
                f'id={pack_id}\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\n'
                'extend=base/game/catalog|catalog.lua\nextend=base/game/sounds|sounds.lua\n'
                + ''.join(f'asset={prefix}{name[7:]}|{name}\n' for name in assets)
            ),
            'catalog.lua': (
                'return function(base)\n'
                f' base.source_path="{prefix}{recipe["source"][7:]}"\n'
                f' base.stage_path="{prefix}{recipe["stage"][7:]}"\n'
                f' base.profile_id="{pack_id}"\n return base\nend\n'
            ),
            'sounds.lua': SOUNDS,
        }
        for name, contents in adapters.items():
            (destination / name).write_text(contents, encoding='utf-8', newline='\n')
        return manifest, pack_id
