import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from verify_game_bundle import validate_bundle


class BundleContractTest(unittest.TestCase):
    def fixture(self, path, manifest_first=True, payload=b'content'):
        digest=hashlib.sha256(b'content').hexdigest()
        body=json.dumps(dict(schema=1,files=[dict(path='scripts/start.lua',sha256=digest,bytes=7)])).encode()
        with ZipFile(path,'w') as archive:
            if manifest_first:archive.writestr('manifest.json',body)
            archive.writestr('blobs/'+digest,payload)
            if not manifest_first:archive.writestr('manifest.json',body)
        return hashlib.sha256(body).hexdigest()

    def test_valid_stream_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bundle.zip';version=self.fixture(path)
            self.assertTrue(validate_bundle(path,version)['manifest_first'])

    def test_manifest_at_end_is_rejected_even_when_crc_and_hash_are_valid(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bundle.zip';version=self.fixture(path,False)
            with ZipFile(path) as archive:self.assertIsNone(archive.testzip())
            with self.assertRaisesRegex(ValueError,'first ZIP entry'):validate_bundle(path,version)

    def test_changed_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bundle.zip';version=self.fixture(path,payload=b'corrupt')
            with self.assertRaisesRegex(ValueError,'SHA256'):validate_bundle(path,version)
