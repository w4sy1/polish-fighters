"""Static asset recovery with evbunpack 0.2.6; never restores or runs an executable."""
import argparse
import hashlib
import json
from pathlib import Path
from evbunpack import __main__ as evb

ALLOWED = {'.bmp', '.png', '.wav', '.dat', '.txt', '.wma', '.mp3', '.ogg'}


def recover(source, destination, legacy=False, extensions=None):
    source = Path(source).resolve(strict=True)
    root = Path(destination).resolve()
    if root.exists():
        raise ValueError('Choose a new destination')
    root.mkdir(parents=True)
    original = evb.process_file_node
    report = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'tool': 'evbunpack 0.2.6', 'executable_executed': False,
              'executable_restored': False, 'files': [], 'skipped': []}
    total = 0
    def write(fd, path, node):
        nonlocal total
        target = Path(path).resolve()
        if not target.is_relative_to(root):
            raise ValueError('Virtual file escapes destination')
        if target.suffix.lower() not in (extensions if extensions is not None else ALLOWED):
            report['skipped'].append(target.relative_to(root).as_posix())
            return
        size = node['original_size']
        total += size
        if size > 64*1024*1024 or total > 2*1024*1024*1024 or len(report['files']) >= 10000:
            raise ValueError('Extraction size/count limit exceeded')
        if target.exists():
            raise ValueError('Duplicate virtual path')
        original(fd, str(target), node)
        if target.stat().st_size != size:
            raise ValueError('Recovered size mismatch')
        report['files'].append({'path': target.relative_to(root).as_posix(), 'size': size,
                               'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    evb.process_file_node = write
    try:
        evb.unpack_files(str(source), str(root), legacy, False)
        if not report['files']:
            raise ValueError('No data recovered')
    finally:
        evb.process_file_node = original
        (root / 'RECOVERY.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('--legacy', action='store_true')
    parser.add_argument('--source-scripts-only', action='store_true', help='Recover AI/source scripts as inert text, not executables')
    args = parser.parse_args()
    result = recover(args.source, args.destination, args.legacy, {'.as', '.lua'} if args.source_scripts_only else None)
    print('Recovered data files:', len(result['files']), '; skipped:', len(result['skipped']))
