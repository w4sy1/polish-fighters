import sys
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_content import audit


class ContentAuditTest(unittest.TestCase):
    def test_existing_packs_have_full_catalogs(self):
        for name, count in [('ntsd', 42), ('lf4-turbo', 32)]:
            report = audit(ROOT / 'content-packs' / name)
            self.assertEqual(report['fighters'], count)
            self.assertFalse(report['missing_assets'])
            self.assertTrue(report['arenas'])
            self.assertTrue(report['campaigns'])
            self.assertFalse(any(x['missing'] for x in report['objects']))

    def test_manifest_cannot_escape_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'package.manifest').write_text('asset=evil|../outside.dat\n')
            with self.assertRaises(ValueError):
                audit(root)

    def test_duplicate_asset_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'package.manifest').write_text('asset=x|a.dat\nasset=x|b.dat\n')
            with self.assertRaises(ValueError):
                audit(root)


if __name__ == '__main__':
    unittest.main()
