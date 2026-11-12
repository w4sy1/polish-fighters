"""Validate the exact ZIP contract consumed by Android's streaming bootstrap reader."""
import hashlib
import json
from pathlib import PurePosixPath
import re
from zipfile import ZipFile


def validate_bundle(path, bundle_id):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        if not entries or entries[0].filename != 'manifest.json' or entries[0].header_offset != 0:
            raise ValueError('manifest.json must be the first ZIP entry: Android reads this archive sequentially')
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate bundle ZIP entries')
        manifest_bytes = archive.read('manifest.json')
        if hashlib.sha256(manifest_bytes).hexdigest() != bundle_id.strip():
            raise ValueError('Manifest does not match game-bundle.id')
        manifest = json.loads(manifest_bytes)
        if manifest.get('schema') != 1 or not 0 < len(manifest.get('files', [])) <= 30000:
            raise ValueError('Invalid bundle schema or file count')
        payloads, paths = {}, set()
        for item in manifest['files']:
            name, digest, size = item['path'], item['sha256'], item['bytes']
            parts = PurePosixPath(name).parts
            if not parts or name.startswith('/') or '\\' in name or '..' in parts or ':' in name or name in paths \
                    or parts[0] in ('.blobs', '.ready') or not re.fullmatch('[0-9a-f]{64}', digest) \
                    or not isinstance(size, int) or not 0 <= size <= 512*1024*1024:
                raise ValueError('Invalid or duplicate game resource: '+name)
            paths.add(name)
            if digest in payloads and payloads[digest] != size:
                raise ValueError('Conflicting sizes for shared payload')
            payloads[digest] = size
        if set(names) != {'manifest.json'} | {'blobs/'+digest for digest in payloads}:
            raise ValueError('Missing or unexpected payloads')
        for digest, size in payloads.items():
            info = archive.getinfo('blobs/'+digest)
            if info.file_size != size:
                raise ValueError('Payload length mismatch')
            with archive.open(info) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                    raise ValueError('Payload SHA256 mismatch')
    return dict(manifest_first=True, logical_files=len(paths), verified_payloads=len(payloads))
