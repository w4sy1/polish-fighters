"""Bounded, data-only ZIP inspection and extraction. Never executes archive content."""
import hashlib
import os
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_FILES = 20000
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_ARCHIVE_BYTES = 1024 * 1024 * 1024
MAX_RATIO = 200
DATA_SUFFIXES = {'.dat', '.txt', '.bmp', '.png', '.jpg', '.jpeg', '.wav', '.ogg', '.mp3', '.wma', '.json', '.md', '.ini', '.cfg'}
RESERVED = re.compile(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)', re.I)


def safe_name(raw):
    if '\\' in raw or '\x00' in raw or ':' in raw or raw.startswith('/'):
        raise ValueError('Unsafe ZIP path: ' + repr(raw))
    parts = raw.rstrip('/').split('/')
    if not parts or any(not part or part in ('.', '..') or part.endswith((' ', '.')) or RESERVED.match(part) or any(ord(c) < 32 or c in '<>"|?*' for c in part) for part in parts):
        raise ValueError('Unsafe ZIP path: ' + repr(raw))
    return PurePosixPath(*parts).as_posix()


def inspect_zip(archive, data_only=False):
    archive = Path(archive)
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError('Archive exceeds size limit')
    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        if len(infos) > MAX_FILES:
            raise ValueError('Too many ZIP entries')
        names = {}; files = []; excluded = []; total = 0; extracted_total = 0
        for entry in infos:
            name = safe_name(entry.orig_filename)
            key = name.casefold()
            if key in names:
                raise ValueError('Duplicate/case-colliding ZIP path: ' + name)
            mode = entry.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or (kind == stat.S_IFDIR and not entry.is_dir()) or (kind == stat.S_IFREG and entry.is_dir()):
                raise ValueError('Links and special files are forbidden: ' + name)
            if entry.flag_bits & 1:
                raise ValueError('Encrypted ZIP entries are unsupported')
            if entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError('Unsupported ZIP compression')
            names[key] = entry.is_dir()
            if entry.is_dir():
                continue
            total += entry.file_size
            if entry.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or entry.file_size > max(1, entry.compress_size) * MAX_RATIO:
                raise ValueError('ZIP expansion limit exceeded')
            if Path(name).suffix.lower() not in DATA_SUFFIXES:
                if not data_only: raise ValueError('Unsupported or executable file: ' + name)
                excluded.append({'name': name, 'bytes': entry.file_size, 'reason': 'executable_or_unsupported'})
                continue
            files.append({'name': name, 'bytes': entry.file_size})
            extracted_total += entry.file_size
        for key in names:
            for parent in PurePosixPath(key).parents:
                if str(parent) in names and not names[str(parent)]:
                    raise ValueError('ZIP file/directory collision')
        if not files:
            raise ValueError('Archive has no supported data files')
        roots = [str(PurePosixPath(f['name']).parent.parent) for f in files
                 if tuple(part.lower() for part in PurePosixPath(f['name']).parts[-2:]) == ('data', 'data.txt')]
        return {'files': files, 'total_bytes': extracted_total, 'archive_expanded_bytes': total,
                'excluded': excluded, 'legacy_roots': roots, 'compatibility': 'not_tested'}


def extract_zip(archive, destination, data_only=False):
    """Publish to a new directory only after all entries pass CRC and byte limits."""
    archive = Path(archive).resolve(strict=True)
    report = inspect_zip(archive, data_only=data_only)
    destination = Path(destination).absolute()
    parent = destination.parent.resolve(strict=True)
    if parent != destination.parent or destination.exists() or destination.is_symlink():
        raise ValueError('Destination must be new and have a real, existing parent')
    if shutil.disk_usage(parent).free < report['total_bytes'] + 16 * 1024 * 1024:
        raise ValueError('Insufficient free disk space')
    stage = Path(tempfile.mkdtemp(prefix='.mod-staging-', dir=parent))
    try:
        with zipfile.ZipFile(archive) as bundle:
            for item in report['files']:
                target = stage / item['name']
                target.parent.mkdir(parents=True, exist_ok=True)
                count = 0
                with bundle.open(item['name']) as source, target.open('xb') as output:
                    while chunk := source.read(1024 * 1024):
                        count += len(chunk)
                        if count > item['bytes'] or count > MAX_FILE_BYTES:
                            raise ValueError('ZIP entry exceeds declared size')
                        output.write(chunk)
                if count != item['bytes']:
                    raise ValueError('Truncated ZIP entry')
        if destination.exists() or destination.is_symlink():
            raise ValueError('Destination already exists')
        os.rename(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    with archive.open('rb') as source:
        report['sha256'] = hashlib.file_digest(source, 'sha256').hexdigest()
    return report
