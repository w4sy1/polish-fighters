import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_native_identity import signature, verify


class NativeIdentityTest(unittest.TestCase):
    def test_paths_and_crlf_do_not_change_identity_but_native_changes_do(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, contents in [('a', b'int a;\n'), ('b', b'int a;\r\n')]:
                (root / name / 'src').mkdir(parents=True)
                (root / name / 'src/a.cpp').write_bytes(contents)
            self.assertEqual(signature(root/'a'), signature(root/'b'))
            binary=root/'libmain.so'; binary.write_bytes(b'ELF'+signature(root/'a').encode())
            self.assertEqual(verify(root/'a',binary),signature(root/'a'))
            (root/'a/src/a.cpp').write_text('int changed;')
            with self.assertRaisesRegex(ValueError, 'Stara biblioteka'): verify(root/'a',binary)
