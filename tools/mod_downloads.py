"""Persistent, sequential archive queue. No downloaded code is ever executed."""
import contextlib
import datetime
import hashlib
import http.client
import json
import os
import re
import shutil
import sqlite3
import time
import uuid
from pathlib import Path
from mod_http import open_public, validate_url

MAX_BYTES = 1024 * 1024 * 1024
RESERVE = 32 * 1024 * 1024


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@contextlib.contextmanager
def worker_lock(path):
    with path.open('a+b') as stream:
        if stream.seek(0, 2) == 0: stream.write(b'0'); stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error: raise ValueError('Another download worker is running') from error
        else:
            import fcntl
            try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error: raise ValueError('Another download worker is running') from error
        try: yield
        finally:
            if os.name == 'nt':
                stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(stream, fcntl.LOCK_UN)


class Queue:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / 'downloads.sqlite3', timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, mod_id TEXT, url TEXT NOT NULL, status TEXT NOT NULL,
            received INTEGER DEFAULT 0, total INTEGER, etag TEXT, modified TEXT,
            result_path TEXT, sha256 TEXT, expected_sha256 TEXT, attempts INTEGER DEFAULT 0,
            error TEXT, created TEXT, updated TEXT)''')
        self.db.commit()

    def close(self): self.db.close()

    def jobs(self):
        return [dict(row) for row in self.db.execute('SELECT * FROM jobs ORDER BY created')]

    def job(self, identifier):
        row = self.db.execute('SELECT * FROM jobs WHERE id=?', (identifier,)).fetchone()
        if row is None: raise ValueError('Unknown download ID')
        return dict(row)

    def _write(self, identifier, **fields):
        allowed = {'status','received','total','etag','modified','result_path','sha256','attempts','error'}
        if not fields.keys() <= allowed: raise ValueError('Invalid job update')
        fields['updated'] = now()
        self.db.execute('UPDATE jobs SET ' + ','.join(key + '=?' for key in fields) + ' WHERE id=?', (*fields.values(), identifier))
        self.db.commit()

    def add(self, url, mod_id=None, expected_sha256=None):
        url = validate_url(url)
        if expected_sha256 and not re.fullmatch('[a-fA-F0-9]{64}', expected_sha256):
            raise ValueError('Reference SHA-256 must contain exactly 64 hexadecimal characters')
        expected_sha256 = expected_sha256.lower() if expected_sha256 else None
        # A repeated click does not enqueue another copy of the same reference.
        for row in self.jobs():
            if row['url'] == url and row['expected_sha256'] == expected_sha256 and row['status'] != 'cancelled': return row
        identifier = uuid.uuid4().hex
        self.db.execute('INSERT INTO jobs(id,mod_id,url,status,expected_sha256,created,updated) VALUES(?,?,?,?,?,?,?)',
                        (identifier, mod_id, url, 'queued', expected_sha256, now(), now()))
        self.db.commit()
        return self.job(identifier)

    def control(self, identifier, action):
        job = self.job(identifier)
        if action == 'pause' and job['status'] in ('queued', 'downloading'):
            self._write(identifier, status='paused')
        elif action == 'resume' and job['status'] in ('paused', 'failed'):
            self._write(identifier, status='queued', error=None, attempts=0)
        elif action == 'cancel' and job['status'] != 'completed':
            self._write(identifier, status='cancelled')
            # Never delete a file held by the transfer thread on Windows.
            try:
                with worker_lock(self.directory / 'worker.lock'):
                    self._part(identifier).unlink(missing_ok=True)
            except ValueError:
                pass  # Active worker deletes it after observing cancellation.
        else: raise ValueError('Action is not valid for this job state')
        return self.job(identifier)

    def _part(self, identifier):
        if not re.fullmatch('[a-f0-9]{32}', identifier): raise ValueError('Invalid download ID')
        result = self.directory / (identifier + '.part')
        if result.is_symlink(): raise ValueError('Download file cannot be a symlink')
        return result

    def _active(self, identifier):
        return self.job(identifier)['status'] == 'downloading'

    def _progress(self, identifier, received, total):
        self.db.execute('UPDATE jobs SET received=?,total=?,updated=? WHERE id=? AND status=?', (received, total, now(), identifier, 'downloading'))
        self.db.commit()

    def _transfer(self, identifier, progress):
        job = self.job(identifier); part = self._part(identifier)
        offset = part.stat().st_size if part.exists() else 0
        validator = job['etag'] if job['etag'] and not job['etag'].startswith('W/') else job['modified']
        if offset > MAX_BYTES: raise ValueError('Partial file exceeds download limit')
        if offset and not validator:
            part.unlink(); offset = 0
        if offset and offset == job['total']:
            # All announced bytes may have reached disk before a process stopped
            # during finalization. Avoid an invalid bytes=EOF Range request (416).
            self._finish(identifier, part, offset, progress)
            return
        headers = {'Range': 'bytes=' + str(offset) + '-', 'If-Range': validator} if offset else {}
        with open_public(job['url'], headers) as response:
            if not self._active(identifier): return
            if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
                raise ValueError('Compressed HTTP responses are not supported for resumable downloads')
            if response.headers.get_content_type() in ('text/html', 'application/xhtml+xml', 'application/json', 'text/plain'):
                raise ValueError('Link returned a page instead of an archive; open the source manually')
            if response.status == 206:
                content_range = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                if not offset or not content_range or int(content_range[1]) != offset:
                    raise ValueError('Server returned an invalid resume range')
                start, end, total = map(int, content_range.groups())
                if end < start or end >= total or end != total - 1:
                    raise ValueError('Server returned an incomplete resume range')
                current_validator = response.headers.get('ETag') if validator == job['etag'] else response.headers.get('Last-Modified')
                if current_validator and current_validator != validator:
                    raise ValueError('Remote archive changed; cancel and enqueue a new download')
                if job['total'] is not None and total != job['total']:
                    raise ValueError('Remote archive size changed')
            elif response.status == 200:
                offset = 0
                length = response.headers.get('Content-Length')
                total = int(length) if length is not None else None
            else: raise ValueError('Unexpected HTTP download status: ' + str(response.status))
            if total is not None and (total < offset or total > MAX_BYTES): raise ValueError('Archive exceeds size limit')
            if shutil.disk_usage(self.directory).free < (total - offset if total else RESERVE) + RESERVE:
                raise ValueError('Insufficient disk space')
            self._write(identifier, etag=response.headers.get('ETag'), modified=response.headers.get('Last-Modified'), total=total)
            received = offset
            last_progress = 0
            with part.open('ab' if offset else 'wb') as output:
                while self._active(identifier):
                    chunk = response.read(256 * 1024)
                    if not chunk: break
                    received += len(chunk)
                    if received > MAX_BYTES or (total is not None and received > total): raise ValueError('Download exceeds declared size or limit')
                    if shutil.disk_usage(self.directory).free < len(chunk) + RESERVE: raise ValueError('Insufficient disk space')
                    output.write(chunk); output.flush()
                    if time.monotonic() - last_progress >= 0.5 or received == total:
                        last_progress = time.monotonic()
                        self._progress(identifier, received, total)
                        progress({'id': identifier, 'received': received, 'total': total, 'status': 'downloading'})
            if not self._active(identifier): return
            if total is not None and received != total: raise OSError('Download ended before declared size')
        self._finish(identifier, part, received, progress)

    def _finish(self, identifier, part, received, progress):
        job = self.job(identifier)
        # Classify bytes, never an untrusted filename or Content-Disposition value.
        with part.open('rb') as stream:
            magic = stream.read(8)
            suffix = '.zip' if magic.startswith((b'PK\x03\x04', b'PK\x05\x06')) else '.7z' if magic.startswith(b'7z\xbc\xaf\x27\x1c') else '.rar' if magic.startswith(b'Rar!\x1a\x07') else None
            stream.seek(0); digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if suffix is None:
            part.unlink(); self._write(identifier, etag=None, modified=None, received=0)
            raise ValueError('Downloaded content is not a supported archive')
        if job['expected_sha256'] and digest != job['expected_sha256']:
            part.unlink(); self._write(identifier, etag=None, modified=None, received=0)
            raise ValueError('Reference SHA-256 mismatch')
        # Equal bytes can be reused, but are not marked safe or compatible.
        duplicate = next((row for row in self.jobs() if row['id'] != identifier and row['status'] == 'completed' and row['sha256'] == digest and row['result_path'] and Path(row['result_path']).is_file()), None)
        target = Path(duplicate['result_path']) if duplicate else self.directory / (identifier + suffix)
        # Serialize final publication with pause/cancel from another connection.
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if not self._active(identifier): self.db.rollback(); return
            if duplicate: part.unlink()
            else:
                if target.exists() or target.is_symlink(): raise ValueError('Download target already exists')
                part.rename(target)
            self._write(identifier, status='completed', result_path=str(target), sha256=digest, received=received, total=received, error=None)
        except BaseException:
            self.db.rollback(); raise
        progress({'id': identifier, 'status': 'completed', 'path': str(target)})

    def run(self, progress=None):
        progress = progress or (lambda event: print(json.dumps(event), flush=True))
        with worker_lock(self.directory / 'worker.lock'):
            # Interrupted process: retained bytes are resumed only on explicit request.
            for job in self.jobs():
                if job['status'] == 'downloading': self._write(job['id'], status='paused', error='Previous worker was interrupted; resume explicitly')
                if job['status'] == 'cancelled': self._part(job['id']).unlink(missing_ok=True)
            for queued in self.jobs():
                identifier = queued['id']
                if self.job(identifier)['status'] != 'queued': continue
                self.db.execute('UPDATE jobs SET status=?,updated=? WHERE id=? AND status=?', ('downloading', now(), identifier, 'queued')); self.db.commit()
                for attempt in range(1, 4):
                    if not self._active(identifier): break
                    self._write(identifier, attempts=attempt)
                    try:
                        self._transfer(identifier, progress); break
                    except KeyboardInterrupt:
                        if self._active(identifier): self._write(identifier, status='paused', error='Interrupted by user')
                        raise
                    except (OSError, ValueError, http.client.HTTPException) as problem:
                        if not self._active(identifier): break
                        self._write(identifier, error=str(problem)[:300])
                        progress({'id': identifier, 'status': 'error', 'message': str(problem)[:300], 'attempt': attempt})
                        if isinstance(problem, ValueError) or attempt == 3:
                            self._write(identifier, status='failed'); break
                        time.sleep(min(4, attempt * 2))
                if self.job(identifier)['status'] == 'cancelled': self._part(identifier).unlink(missing_ok=True)
