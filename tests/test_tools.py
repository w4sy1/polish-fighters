import importlib.util
from pathlib import Path
import tempfile
import unittest
spec = importlib.util.spec_from_file_location('pf', Path(__file__).resolve().parents[1] / 'tools/pf.py')
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
    def catalog(self, source):
        (self.root / 'data/data.txt').write_text(source)
    def test_inventory_missing_and_duplicate_ids(self):
        (self.root / 'data/a.dat').write_bytes(b'synthetic')
        self.catalog('<object>\nid: 1 type: 0 file: data/a.dat\nid: 1 type: 1 file: data/missing.dat\n<object_end>')
        result = pf.inspect_pack(self.root)
        self.assertEqual(result['fighters'], 1)
        self.assertEqual(result['duplicate_object_ids'], [1])
        self.assertEqual(result['missing_catalog_files'], ['data/missing.dat'])
        self.assertFalse(result['ready_to_merge'])
        self.assertEqual(len(result['objects'][0]['sha256']), 64)
    def test_escape_paths_rejected(self):
        for path in ['../secret', '/etc/passwd', 'C:\\secret']:
            with self.subTest(path=path):
                self.catalog(f'id: 1 type: 0 file: {path}')
                with self.assertRaises(ValueError): pf.inspect_pack(self.root)
    def test_symlink_escape_rejected(self):
        outside = self.root.parent / (self.root.name + '-outside.txt')
        outside.write_text('outside fixture')
        self.addCleanup(outside.unlink, missing_ok=True)
        try:
            (self.root / 'data/out').symlink_to(outside)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows requires symlink privileges for this test')
            raise
        self.catalog('id: 1 type: 0 file: data/out')
        with self.assertRaises(ValueError): pf.inspect_pack(self.root)
    def test_backgrounds_and_windows_paths(self):
        self.catalog('id: 1 type: 0 file: data\\fighter.dat\nid: 0 file: bg\\arena.txt')
        result = pf.inspect_pack(self.root)
        self.assertEqual(result['backgrounds'][0]['path'], 'bg/arena.txt')
    def test_legacy_trailing_notes_outside_catalog_sections(self):
        self.catalog('<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n'
                     '<background>\nid: 0 file: bg/arena.txt\n<background_end>\n'
                     'data\\nothing.txt\nLegacy notes are not catalog entries')
        result = pf.inspect_pack(self.root)
        self.assertEqual(result['fighters'], 1)
        self.assertEqual(len(result['backgrounds']), 1)
        self.catalog('<object>\nunsupported inside section\n<object_end>')
        with self.assertRaises(ValueError):
            pf.inspect_pack(self.root)
    def test_launcher_uses_arguments_without_shell(self):
        binary = self.root / 'engine with spaces.exe'; binary.touch()
        installer = self.root / 'installer.exe'; installer.touch()
        calls=[]
        class Result: returncode=0
        def run(args, **kwargs):
            calls.append((args, kwargs)); return Result()
        self.assertEqual(pf.launch(binary, installer, run=run), 0)
        self.assertTrue(Path(calls[0][0][0]).samefile(binary))
        self.assertIn('--mod', calls[0][0])
        self.assertEqual(Path(calls[0][0][-1]), pf.ROOT / 'engine/scripts/polish-fighters')
        self.assertNotIn('shell', calls[0][1])

if __name__ == '__main__': unittest.main()
