"""Managed data packages, reversible changes and explicit desktop launch plans.

No third-party scripts are accepted here: packages must come from our LF2 converter.
Structural checks are not gameplay tests and never grant compatibility status.
"""
import contextlib
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path
from mod_downloads import worker_lock
from mod_archive import inspect_zip

MAX_STATE = 2 * 1024 * 1024


def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{1,40}', value):
        raise ValueError('Invalid managed identifier')
    return value


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory_digest(hashes):
    return hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    if path.is_symlink(): raise ValueError('State file cannot be a symlink')
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode('utf-8') + b'\n'
    if len(raw) > MAX_STATE: raise ValueError('Manager state exceeds its size limit')
    temporary = path.with_name('.' + path.name + '-' + uuid.uuid4().hex)
    try:
        with temporary.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Library:
    def __init__(self, home):
        self.home = Path(home).absolute()
        self.home.mkdir(parents=True, exist_ok=True)
        if self.home.resolve() != self.home: raise ValueError('Library root cannot use links or junctions')
        for name in ('installed', 'versions', 'history', 'profiles'):
            folder = self.home / name
            folder.mkdir(exist_ok=True)
            if folder.resolve() != folder: raise ValueError('Managed directories cannot use links or junctions')
        self.state = self.home / 'library.json'

    @contextlib.contextmanager
    def locked(self):
        try:
            with worker_lock(self.home / 'library.lock'):
                yield
        except ValueError as error:
            if str(error) == 'Another download worker is running':
                raise ValueError('Another library operation is running; try again shortly') from error
            raise

    def read(self):
        if self.state.is_symlink(): raise ValueError('State file cannot be a symlink')
        if not self.state.exists():
            return {'schema_version': 1, 'revision': 0, 'installed': {}, 'archived': {},
                    'profiles': {'default': {'name': 'Domyślny', 'mods': []}}, 'selected_profile': 'default'}
        if self.state.stat().st_size > MAX_STATE: raise ValueError('Library state exceeds size limit')
        data = json.loads(self.state.read_text(encoding='utf-8'))
        if data.get('schema_version') != 1 or not all(isinstance(data.get(key), dict) for key in ('installed', 'archived', 'profiles')):
            raise ValueError('Invalid library state; keep it and restore a known snapshot')
        for group in ('installed', 'archived', 'profiles'):
            for key in data[group]: identifier(key)
        return data

    def save(self, data, operation):
        previous = self.read()
        if self.state.exists():
            snapshot = dict(previous)
            snapshot['snapshot_operation'] = operation
            snapshot['snapshot_time'] = timestamp()
            atomic_json(self.home / 'history' / ('snapshot-' + uuid.uuid4().hex + '.json'), snapshot)
        data['revision'] = previous.get('revision', 0) + 1
        data['updated'] = timestamp()
        atomic_json(self.state, data)

    def assert_idle(self, data):
        # Only inspect processes explicitly started by this manager. A matching
        # live PID blocks moves/updates of resources the engine may still read.
        live = []
        for run in data.get('runs', []):
            pid = int(run['pid'])
            if os.name == 'nt':
                import ctypes
                from ctypes import wintypes
                kernel = ctypes.WinDLL('kernel32', use_last_error=True)
                kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
                kernel.OpenProcess.restype = wintypes.HANDLE
                kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
                kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
                handle = kernel.OpenProcess(0x1000, False, pid)
                if not handle:
                    if ctypes.get_last_error() == 5: live.append(run)
                    continue
                try:
                    code = wintypes.DWORD()
                    if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259: live.append(run)
                finally: kernel.CloseHandle(handle)
            else:
                try: os.kill(pid, 0); live.append(run)
                except ProcessLookupError: pass
                except PermissionError: live.append(run)
        data['runs'] = live
        if live: raise ValueError('Close the game launched by this manager before changing packages or profiles')

    def package_path(self, pack_id):
        path = self.home / 'installed' / identifier(pack_id)
        if path.resolve() != path: raise ValueError('Package path is linked outside the managed library')
        return path

    def hashes(self, directory):
        directory = Path(directory)
        result = {}; total = 0
        for item in directory.rglob('*'):
            if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
                raise ValueError('Linked package paths are forbidden')
            if not item.is_file(): continue
            total += item.stat().st_size
            if total > 2 * 1024 * 1024 * 1024 or len(result) >= 20000:
                raise ValueError('Installed package exceeds resource limits')
            result[item.relative_to(directory).as_posix()] = digest(item)
        return result

    def preview(self, archive):
        result = inspect_zip(archive, data_only=True)
        result['mode'] = 'supported_data_only; executable/unsupported files will not be extracted'
        result['gameplay_verified'] = False
        return result

    def describe(self, path, report, name, catalog_id=None):
        # The converter owns these two scripts. Never adopt an arbitrary native
        # manifest, EXE, DLL, shell script or archive-provided Lua module.
        pack_id = identifier(report['pack_id'])
        manifest = (path / 'package.manifest').read_text(encoding='utf-8')
        required = {'id=' + pack_id, 'version=1', 'api=1', 'requires=base@1', 'requires=polish-fighters@1',
                    'extend=base/game/catalog|catalog.lua', 'extend=base/game/sounds|sounds.lua'}
        lines = manifest.splitlines()
        if not required <= set(lines) or any(line not in required and not line.startswith('asset=') for line in lines):
            raise ValueError('Package does not match the managed converter format')
        hashes = self.hashes(path)
        if {name for name in hashes if name.endswith('.lua')} != {'catalog.lua', 'sounds.lua'}:
            raise ValueError('Unexpected scripts in imported package')
        assets = [line[6:].split('|', 1)[0] for line in lines if line.startswith('asset=')]
        namespace = 'mods/' + pack_id + '/'
        if len(set(assets)) != len(assets) or any(not asset.startswith(namespace) for asset in assets):
            raise ValueError('Conflicting assets or asset outside the package namespace')
        # Keep state snapshots small; a digest covers the entire file inventory.
        # Native virtual paths cannot collide across distinct package IDs.
        object_ids = []
        source_match = re.search(r'base\.source_path="([^"]+)"', (path / 'catalog.lua').read_text(encoding='utf-8'))
        if source_match:
            source = next((line.split('|', 1)[1] for line in lines if line.startswith('asset=' + source_match[1] + '|')), None)
            if source:
                text = (path / source).read_text(encoding='latin1')
                object_ids = [int(value) for value in re.findall(r'(?m)^id:\s*(\d+)\s+type:', text)]
        return {'id': pack_id, 'name': str(name or pack_id)[:120], 'catalog_id': catalog_id,
                'package_api_version': '1', 'version': None, 'installed_at': timestamp(), 'archive_sha256': report.get('archive_sha256'),
                'compatibility': 'not_tested', 'gameplay_verified': False,
                'excluded_files': report.get('excluded_archive_files', []),
                'fighters': report.get('fighters', []), 'objects': report.get('objects'),
                'backgrounds': report.get('backgrounds'), 'assets': len(assets),
                'asset_namespace': namespace, 'object_ids': object_ids,
                'exclusive_targets': ['base/game/catalog', 'base/game/sounds'],
                'inventory_sha256': inventory_digest(hashes)}

    def install(self, archive, name=None, catalog_id=None, update_id=None):
        from mod_manager import import_zip
        # Serialize installs and profile changes; no source/base-game directory is overwritten.
        with self.locked():
            data = self.read()
            self.assert_idle(data)
            if Path(archive).stat().st_size > 1024 * 1024 * 1024: raise ValueError('Archive exceeds size limit')
            # Stable IDs give independent installs of identical archives the same
            # virtual asset paths for the engine's network identity calculation.
            archive_sha256 = digest(archive)
            pack_id = identifier(update_id) if update_id else 'mod-' + archive_sha256[:24]
            previous = data['installed'].get(pack_id)
            if update_id and previous is None: raise ValueError('Cannot update an uninstalled package')
            if not update_id:
                duplicate = next((row for row in data['installed'].values() if row.get('archive_sha256') == archive_sha256), None)
                if duplicate:
                    self.verify(duplicate['id'], data)
                    return {'package': duplicate, 'duplicate': True}
                if previous: raise ValueError('Package ID collision; choose an explicit update instead')
            target = self.package_path(pack_id)
            if target.exists() and not previous: raise ValueError('Unregistered directory blocks installation')
            with tempfile.TemporaryDirectory(prefix='.install-', dir=self.home) as work:
                staging = Path(work) / 'package'
                report = import_zip(archive, staging, pack_id, data_only=True)
                if report['archive_sha256'] != archive_sha256: raise ValueError('Archive changed during installation; select it again')
                record = self.describe(staging, report, name or (previous or {}).get('name') or Path(archive).stem,
                                       catalog_id or (previous or {}).get('catalog_id'))
                backup = None
                if previous:
                    backup = self._version(data, pack_id, previous, 'update')
                    target.rename(backup)
                published = False
                try:
                    if target.exists(): raise ValueError('Installation target already exists')
                    staging.rename(target)
                    published = True
                    data['installed'][pack_id] = record
                    self.save(data, 'update' if previous else 'install')
                except BaseException:
                    # The only recursive deletion here targets our newly created,
                    # unpublished package, whose path is checked by package_path().
                    if published and target.exists():
                        shutil.rmtree(self.package_path(pack_id))
                    if backup and backup.exists(): backup.rename(target)
                    raise
                return {'package': record, 'duplicate': False}

    def _version(self, data, pack_id, record, reason):
        token = 'backup-' + uuid.uuid4().hex
        folder = self.home / 'versions' / token
        data['archived'][token] = {'package_id': pack_id, 'record': record, 'reason': reason, 'time': timestamp()}
        return folder

    def verify(self, pack_id, data=None):
        data = data or self.read()
        record = data['installed'].get(identifier(pack_id))
        if record is None: raise ValueError('Package is not installed')
        actual = self.hashes(self.package_path(pack_id))
        if inventory_digest(actual) != record['inventory_sha256']:
            raise ValueError('Package files changed or are missing: ' + pack_id)
        return record

    def export_android(self, pack_id, destination):
        """Create a transfer ZIP for the Android importer from a verified converted package."""
        pack_id = identifier(pack_id)
        destination = Path(destination).absolute()
        parent = destination.parent.resolve(strict=True)
        if parent != destination.parent or destination.exists() or destination.is_symlink():
            raise ValueError('Export destination must be new and have a real, existing parent')
        self.verify(pack_id)
        source = self.package_path(pack_id)
        temporary = parent / ('.' + destination.name + '.' + uuid.uuid4().hex + '.part')
        total = 0; count = 0
        try:
            with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
                for path in sorted(source.rglob('*')):
                    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                        raise ValueError('Linked package paths are forbidden')
                    if not path.is_file(): continue
                    relative = path.relative_to(source).as_posix()
                    if relative.startswith('../') or '\\' in relative:
                        raise ValueError('Unsafe package path')
                    count += 1; total += path.stat().st_size
                    if count > 20000 or total > 2 * 1024 * 1024 * 1024:
                        raise ValueError('Package exceeds Android transfer limits')
                    output.write(path, pack_id + '/' + relative)
            if destination.exists() or destination.is_symlink(): raise ValueError('Export destination already exists')
            os.rename(temporary,destination)
            return {'id': pack_id, 'path': str(destination), 'bytes': destination.stat().st_size,
                    'sha256': digest(destination), 'gameplay_verified': False}
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

    def conflicts(self, mods, data=None, verify_files=False):
        data = data or self.read()
        if len(mods) > 62: raise ValueError('At most 62 managed packages can be selected')
        problems = []; owners = {}; assets = {}; object_ids = {}; total_assets = 1
        for pack_id in mods:
            identifier(pack_id)
            if pack_id in owners: problems.append('Powtórzony pakiet: ' + pack_id); continue
            owners[pack_id] = True
            record = data['installed'].get(pack_id)
            if not record: problems.append('Brak zainstalowanego pakietu: ' + pack_id); continue
            if verify_files:
                try: self.verify(pack_id, data)
                except (ValueError, OSError) as error: problems.append(str(error))
            for target in record['exclusive_targets']:
                key = 'target:' + target
                if key in owners: problems.append('Konflikt pełnych katalogów/mechanik: ' + owners[key] + ' / ' + pack_id + ' (' + target + ')')
                owners[key] = pack_id
            namespace = record['asset_namespace']
            if namespace in assets: problems.append('Konflikt przestrzeni zasobów: ' + namespace)
            assets[namespace] = pack_id; total_assets += record['assets']
            for key in record['object_ids']:
                if key in object_ids: problems.append('Konflikt identyfikatora obiektu ' + str(key) + ': ' + object_ids[key] + ' / ' + pack_id)
                object_ids[key] = pack_id
        if total_assets > 4096: problems.append('Zestaw przekracza limit 4096 zasobów silnika')
        return problems

    def profile(self, profile_id, name=None, mods=None, select=False):
        profile_id = identifier(profile_id)
        with self.locked():
            data = self.read()
            self.assert_idle(data)
            profile = data['profiles'].get(profile_id, {'name': profile_id, 'mods': []})
            if mods is not None:
                problems = self.conflicts(mods, data, verify_files=True)
                if problems: raise ValueError('\n'.join(problems))
                profile['mods'] = list(mods)
            if name is not None: profile['name'] = str(name)[:120]
            data['profiles'][profile_id] = profile
            if select: data['selected_profile'] = profile_id
            self.save(data, 'profile')
            return profile

    def toggle(self, pack_id, enabled, profile_id=None):
        with self.locked():
            data = self.read(); profile_id = identifier(profile_id or data['selected_profile'])
            self.assert_idle(data)
            profile = data['profiles'].get(profile_id)
            if profile is None: raise ValueError('Unknown profile')
            mods = [item for item in profile['mods'] if item != pack_id]
            if enabled: mods.append(identifier(pack_id))
            problems = self.conflicts(mods, data, verify_files=enabled)
            if problems: raise ValueError('\n'.join(problems))
            profile['mods'] = mods; self.save(data, 'enable' if enabled else 'disable')
            return profile

    def remove(self, pack_id):
        with self.locked():
            data = self.read(); pack_id = identifier(pack_id)
            self.assert_idle(data)
            record = data['installed'].get(pack_id)
            if record is None: raise ValueError('Package is not installed')
            target = self.package_path(pack_id)
            backup = self._version(data, pack_id, record, 'remove')
            target.rename(backup)
            try:
                del data['installed'][pack_id]
                for profile in data['profiles'].values(): profile['mods'] = [item for item in profile['mods'] if item != pack_id]
                self.save(data, 'remove')
            except BaseException:
                backup.rename(target); raise
            return {'backup': backup.name, 'restorable': True}

    def restore(self, token):
        token = identifier(token)
        with self.locked():
            data = self.read(); archived = data['archived'].get(token)
            self.assert_idle(data)
            if archived is None: raise ValueError('Unknown package backup')
            pack_id = identifier(archived['package_id']); source = self.home / 'versions' / token
            if source.resolve() != source or not source.is_dir(): raise ValueError('Backup folder is missing or linked')
            if inventory_digest(self.hashes(source)) != archived['record']['inventory_sha256']: raise ValueError('Backup contents changed')
            target = self.package_path(pack_id)
            current = data['installed'].get(pack_id); swapped = None
            if target.exists():
                if not current: raise ValueError('Unregistered directory blocks restore')
                swapped = self._version(data, pack_id, current, 'before-restore')
                target.rename(swapped)
            try:
                source.rename(target)
                data['installed'][pack_id] = archived['record']; del data['archived'][token]
                # Restoring files does not automatically enable a mod in profiles.
                self.save(data, 'restore')
            except BaseException:
                if target.exists(): target.rename(source)
                if swapped and swapped.exists(): swapped.rename(target)
                raise
            return data['installed'][pack_id]

    def snapshot_restore(self, token):
        if not re.fullmatch(r'snapshot-[a-f0-9]{32}', token): raise ValueError('Invalid snapshot token')
        with self.locked():
            path = self.home / 'history' / (token + '.json')
            if path.resolve() != path or path.stat().st_size > MAX_STATE: raise ValueError('Invalid snapshot path')
            snapshot = json.loads(path.read_text(encoding='utf-8')); data = self.read()
            self.assert_idle(data)
            # Restore profile choices only. File versions have their separate,
            # explicit restore path, so metadata never claims absent files exist.
            for profile_id, profile in snapshot['profiles'].items():
                identifier(profile_id)
                problems = self.conflicts(profile['mods'], data, verify_files=True)
                if problems: raise ValueError('Restore package versions first: ' + '; '.join(problems))
            data['profiles'] = snapshot['profiles']; data['selected_profile'] = identifier(snapshot['selected_profile'])
            self.save(data, 'restore-profile-snapshot'); return data

    def launch_plan(self, executable, scripts, profile_id=None):
        data = self.read(); profile_id = identifier(profile_id or data['selected_profile'])
        profile = data['profiles'].get(profile_id)
        if profile is None: raise ValueError('Unknown profile')
        problems = self.conflicts(profile['mods'], data, verify_files=True)
        if problems: raise ValueError('\n'.join(problems))
        executable = Path(executable).resolve(strict=True)
        if executable.name.lower() not in ('littlefighters.exe', 'openlf2.exe', 'polishlittlefighters.exe') or not executable.is_file():
            raise ValueError('Select LittleFighters.exe or openlf2.exe from the trusted game release, not an installer')
        if self.home == executable or self.home in executable.parents:
            raise ValueError('Never launch an executable from the mod library/downloads')
        scripts = Path(scripts).resolve(strict=True)
        for package in ('base', 'polish-fighters'):
            if not (scripts / package / 'package.manifest').is_file(): raise ValueError('Game scripts are incomplete: ' + package)
        configuration = self.home / 'profiles' / profile_id
        configuration.mkdir(exist_ok=True)
        if configuration.resolve() != configuration: raise ValueError('Profile configuration path cannot be linked')
        arguments = [str(executable), '--scripts', str(scripts), '--config-dir', str(configuration)]
        identity = []
        for pack_id in profile['mods']:
            arguments += ['--mod', str(self.package_path(pack_id))]
            identity.append({'id': pack_id, 'content': data['installed'][pack_id]['inventory_sha256']})
        fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        return {'arguments': arguments, 'cwd': str(executable.parent), 'profile': profile_id,
                'mods_fingerprint': fingerprint, 'compatibility': 'not_tested',
                'network_identity_owner': 'engine: scripts, resources and engine signature'}

    def launch(self, executable, scripts, profile_id=None):
        # Called only by explicit CLI command or the GUI's Play button.
        with self.locked():
            data = self.read(); self.assert_idle(data)
            plan = self.launch_plan(executable, scripts, profile_id)
            process = subprocess.Popen(plan['arguments'], cwd=plan['cwd'], shell=False)
            try:
                data.setdefault('runs', []).append({'pid': process.pid, 'executable': str(Path(executable).resolve()), 'time': timestamp()})
                self.save(data, 'launch')
            except BaseException:
                process.terminate(); raise
            return {'pid': process.pid, 'profile': plan['profile'], 'compatibility': 'not_tested'}
