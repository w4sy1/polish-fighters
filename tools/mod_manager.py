"""Mod registry, on-demand source discovery, download queue and isolated LF2 import."""
import argparse
import json
import re
import tempfile
import zipfile
from pathlib import Path
from mod_archive import inspect_zip, extract_zip
from import_legacy import convert
from mod_downloads import Queue
from mod_sources import discover, sources

ROOT = Path(__file__).resolve().parents[1]


def catalog(query='', category=None):
    entries = json.loads((ROOT / 'data/mods/catalog.json').read_text(encoding='utf-8'))['entries']
    query = query.casefold()
    return [entry for entry in entries if (category is None or entry['category'] == category) and query in ' '.join([entry['name'], entry['author'] or '', *entry['characters']]).casefold()]


def import_zip(archive, destination, pack_id, data_only=False):
    """Explicit import never activates a mod or changes base-game resources."""
    if not re.fullmatch(r'[a-z][a-z0-9-]{1,40}', pack_id):
        raise ValueError('Invalid package ID')
    destination = Path(destination).absolute()
    parent = destination.parent.resolve(strict=True)
    if parent != destination.parent or destination.exists() or destination.is_symlink():
        raise ValueError('Destination must be new and have a real, existing parent')
    preview = inspect_zip(archive, data_only=data_only)
    if len(preview['legacy_roots']) != 1:
        raise ValueError('Expected exactly one LF2 data/data.txt catalogue')
    # Both extraction and conversion stay under a temporary sibling directory.
    with tempfile.TemporaryDirectory(prefix='.mod-import-', dir=parent) as temporary:
        temporary = Path(temporary)
        report = extract_zip(archive, temporary / 'source', data_only=data_only)
        source = temporary / 'source' / preview['legacy_roots'][0]
        result = convert(source, temporary / 'package', pack_id)
        result.update(archive_sha256=report['sha256'], compatibility='not_tested', active=False)
        if report.get('excluded'): result['excluded_archive_files'] = report['excluded']
        (temporary / 'package' / 'import-report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if destination.exists() or destination.is_symlink():
            raise ValueError('Destination already exists')
        (temporary / 'package').rename(destination)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list')
    listing.add_argument('--query', default='')
    listing.add_argument('--category')
    preview = commands.add_parser('inspect')
    preview.add_argument('archive')
    importer = commands.add_parser('import')
    importer.add_argument('archive'); importer.add_argument('destination'); importer.add_argument('--id', required=True)
    importer.add_argument('--data-only', action='store_true', help='Explicitly skip executable and unsupported archive entries; import supported data only')
    commands.add_parser('sources')
    discovery = commands.add_parser('discover')
    discovery.add_argument('source', choices=[item['id'] for item in sources()])
    discovery.add_argument('--page')
    discovery.add_argument('--output', type=Path, help='Optional local discovery report')
    downloads = commands.add_parser('downloads')
    downloads.add_argument('action', choices=['add', 'list', 'run', 'pause', 'resume', 'cancel'])
    downloads.add_argument('--directory', type=Path, default=ROOT / 'userdata/mod-manager/downloads')
    downloads.add_argument('--url'); downloads.add_argument('--id'); downloads.add_argument('--mod-id'); downloads.add_argument('--sha256')
    library = commands.add_parser('library')
    library.add_argument('action', choices=['list','install','update','remove','restore','profile','enable','disable','conflicts','history','restore-profile','export-android','plan','launch'])
    library.add_argument('--home', type=Path, default=ROOT / 'userdata/mod-manager')
    library.add_argument('--archive'); library.add_argument('--id'); library.add_argument('--name'); library.add_argument('--catalog-id'); library.add_argument('--output')
    library.add_argument('--profile', default='default'); library.add_argument('--mods', nargs='*')
    library.add_argument('--exe'); library.add_argument('--scripts', type=Path, default=ROOT / 'engine/scripts')
    args = parser.parse_args()
    try:
        if args.command == 'list': result = catalog(args.query, args.category)
        elif args.command == 'inspect': result = inspect_zip(args.archive)
        elif args.command == 'import': result = import_zip(args.archive, args.destination, args.id, args.data_only)
        elif args.command == 'sources': result = sources()
        elif args.command == 'discover':
            result = discover(args.source, args.page)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        elif args.command == 'library':
            from mod_library import Library
            library = Library(args.home)
            if args.action == 'list': result = library.read()
            elif args.action in ('install','update'):
                if not args.archive: raise ValueError('Installation requires --archive')
                if args.action == 'update' and not args.id: raise ValueError('Update requires --id')
                result = library.install(args.archive, args.name, args.catalog_id, args.id if args.action == 'update' else None)
            elif args.action == 'profile': result = library.profile(args.profile, args.name, args.mods, select=True)
            elif args.action in ('enable','disable'):
                if not args.id: raise ValueError('Enable/disable requires --id')
                result = library.toggle(args.id, args.action == 'enable', args.profile)
            elif args.action in ('remove','restore','restore-profile'):
                if not args.id: raise ValueError('Action requires --id')
                result = {'remove': library.remove, 'restore': library.restore, 'restore-profile': library.snapshot_restore}[args.action](args.id)
            elif args.action == 'export-android':
                if not args.id or not args.output: raise ValueError('Android export requires --id and --output')
                result = library.export_android(args.id,args.output)
            elif args.action == 'conflicts': result = library.conflicts(args.mods or [], verify_files=True)
            elif args.action == 'history': result = [path.stem for path in sorted((library.home / 'history').glob('snapshot-*.json'))]
            else:
                if not args.exe: raise ValueError('Launch/plan requires --exe pointing to the trusted game')
                operation = library.launch if args.action == 'launch' else library.launch_plan
                result = operation(args.exe, args.scripts, args.profile)
        else:
            queue = Queue(args.directory)
            try:
                if args.action == 'add':
                    if not args.url: raise ValueError('Adding a download requires --url with an explicit direct archive URL')
                    result = queue.add(args.url, args.mod_id, args.sha256)
                elif args.action == 'list': result = queue.jobs()
                elif args.action == 'run': queue.run(); result = queue.jobs()
                else:
                    if not args.id: raise ValueError('Download action requires --id')
                    result = queue.control(args.id, args.action)
            finally: queue.close()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, AttributeError, EOFError, zipfile.BadZipFile, RuntimeError) as problem:
        parser.exit(1, str(problem) + '\n')


if __name__ == '__main__':
    main()
