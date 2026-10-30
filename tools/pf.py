#!/usr/bin/env python3
"""Offline developer CLI; no dependencies outside Python 3.10+."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def inspect_pack(folder):
    root = Path(folder).resolve(strict=True)
    index = root / 'data' / 'data.txt'
    if not index.is_file():
        raise ValueError('Expected an extracted LF2 folder containing data/data.txt')
    objects, backgrounds, missing, seen, duplicates = [], [], [], set(), []
    catalog = index.read_text(encoding='utf-8-sig', errors='replace')
    sectioned = '<object>' in catalog or '<background>' in catalog
    in_section = not sectioned
    for raw in catalog.splitlines():
        line = raw.split('#', 1)[0].strip()
        if line in ('<object>', '<background>'):
            in_section = True
            continue
        if line in ('<object_end>', '<background_end>'):
            in_section = False
            continue
        if not in_section:
            continue
        match = re.fullmatch(r'id:\s*(\d+)\s+(?:type:\s*(\d+)\s+)?file:\s*(\S+)', line)
        if not match:
            if line and not line.startswith('<'):
                raise ValueError(f'Unsupported catalog line: {line}')
            continue
        id_, kind, source = match.groups()
        rel = PurePosixPath(source.replace('\\', '/'))
        if rel.is_absolute() or '..' in rel.parts or ':' in source:
            raise ValueError(f'Unsafe resource path: {source}')
        target = root.joinpath(*rel.parts).resolve()
        if not target.is_relative_to(root):
            raise ValueError(f'Resource escapes folder: {source}')
        entry = {'id': int(id_), 'path': rel.as_posix()}
        if not target.is_file():
            missing.append(entry['path'])
        else:
            entry['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        if kind is not None:
            entry['type'] = int(kind)
            if entry['id'] in seen:
                duplicates.append(entry['id'])
            seen.add(entry['id'])
            objects.append(entry)
        else:
            backgrounds.append(entry)
    if not objects:
        raise ValueError('Empty object catalog')
    return {'source': str(root), 'objects': objects, 'backgrounds': backgrounds,
            'fighters': sum(e['type'] == 0 for e in objects),
            'missing_catalog_files': missing, 'duplicate_object_ids': duplicates,
            'scope': 'Catalog inventory only; nested assets and gameplay compatibility are not checked',
            'ready_to_merge': False}

def launch(binary, installer, extra=(), run=subprocess.run, pack=None):
    executable = Path(binary).resolve(strict=True)
    data = Path(installer).resolve(strict=True)
    if not executable.is_file() or not data.is_file():
        raise ValueError('Engine and installer must be files')
    selected=[]
    if pack:
        if not re.fullmatch(r'[a-z][a-z0-9-]{1,40}',pack):raise ValueError('Invalid pack ID')
        folder=ROOT/'content-packs'/pack
        if not (folder/'package.manifest').is_file():raise ValueError('Pack is not installed: '+pack)
        selected=['--mod',str(folder)]
    config = ROOT / 'userdata'
    config.mkdir(exist_ok=True)
    return run([str(executable), '--installer', str(data), '--config-dir', str(config),
                '--scripts', str(ROOT / 'engine/scripts'),
                '--mod', str(ROOT / 'engine/scripts/polish-fighters'), *selected, *extra],
               cwd=executable.parent).returncode

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    scan = sub.add_parser('inspect-pack'); scan.add_argument('folder')
    play = sub.add_parser('launch'); play.add_argument('--engine', required=True)
    play.add_argument('--installer', required=True); play.add_argument('--pack')
    args = p.parse_args()
    try:
        if args.command == 'status':
            print((ROOT / 'config/project.json').read_text(encoding='utf-8'))
        elif args.command == 'inspect-pack':
            report = inspect_pack(args.folder)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2 if report['missing_catalog_files'] or report['duplicate_object_ids'] else 0
        else:
            return launch(args.engine, args.installer, pack=args.pack)
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
