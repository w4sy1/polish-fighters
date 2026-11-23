import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mod_archive as archive
import mod_manager as manager
from mod_library import Library
import generate_mod_catalog
from import_legacy import encode


class ModTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.zip = self.root / 'mod.zip'

    def make_zip(self, files):
        with zipfile.ZipFile(self.zip, 'w') as output:
            for name, data in files.items(): output.writestr(name, data)

    def test_registry_and_generated_copy(self):
        rows = manager.catalog()
        self.assertEqual(len(rows), 103)
        self.assertEqual(len({e['id'] for e in rows}), 103)
        self.assertEqual(len(manager.catalog('D.R. LF2 & LF3')), 2)
        self.assertTrue(manager.catalog('NTSD Community Seasons 1–7'))
        # Entries actually imported in this repo (content-packs/<id>) are no longer
        # 'not_tested': they are 'experimental' (statically imported, not gameplay-verified),
        # except one-piece-new-world-0-3 whose source archive is incomplete (compatibility=None).
        imported_experimental = {
            'lf3bytitaszibikas-2-0b', 'ntsd-community-edition', 'dragonball-super-edition-v1-0',
            'one-piece-legends-of-sea-2-1x', 'mortal-kombat-lf2',
        }
        blocked_archive = {'one-piece-new-world-0-3'}
        for entry in rows:
            if entry['id'] in imported_experimental:
                self.assertEqual(entry['compatibility'], 'experimental', entry['id'])
            elif entry['id'] in blocked_archive:
                self.assertIsNone(entry['compatibility'], entry['id'])
            else:
                self.assertEqual(entry['compatibility'], 'not_tested', entry['id'])
        # Three entries have been verified against the real lf-empire.de pages
        # (2026-11-19): their download_url is now known and real, the rest are
        # still unverified placeholders.
        verified_ids = {
            'reinforced-little-fighter-2',
            'naruto-lf2-v2-0',
            'wrestle-little-fighter-v1-35-above-limit',
        }
        for entry in rows:
            if entry['id'] in verified_ids:
                self.assertIsNotNone(entry['download_url'], entry['id'])
            else:
                self.assertIsNone(entry['download_url'], entry['id'])
        by_id = {entry['id']: entry for entry in rows}
        # v1-0 was downloaded and imported (content-packs/dragon-ball-super) in this repo;
        # v1-1 is a different, separate version that was never touched.
        self.assertEqual(by_id['dragonball-super-edition-v1-0']['download_status'], 'downloaded')
        self.assertEqual(by_id['dragonball-super-edition-v1-1']['download_status'], 'download_access_blocked')
        self.assertIn('/downloads/', by_id['dragonball-super-edition-v1-1']['download_page_url'])
        bleach = by_id['bleach-bankai-revolution-2-0']
        self.assertEqual(bleach['version'], '2.0')
        self.assertTrue(bleach['download_page_url'].endswith('/versoes-anteriores/'))
        self.assertNotEqual(by_id['ntsd-community-edition']['page_url'],
                            by_id['naruto-the-setting-dawn-2-5']['page_url'])
        self.assertEqual((ROOT / 'engine/scripts/polish-fighters/mod_catalog.lua').read_text(encoding='utf-8'), generate_mod_catalog.render())

    def test_paths(self):
        for name in ('../x.dat', '/x.dat', 'C:/x.dat', 'x\\y.dat', 'con.txt', 'x/COM1.dat', 'x./a.dat', 'x /a.dat', 'a//b.dat', 'a/./b.dat', 'x\x00.dat'):
            with self.subTest(name=name), self.assertRaises(ValueError): archive.safe_name(name)

    def test_ultimate_reads_named_links_from_posts(self):
        thread = 'https://theultimatefighters.forumotion.com/t26-lf2-mods-all'
        markup = '''
            <a href="https://forumotion.com/">Forumotion</a>
            <ul><li>Naruto: Battle For Dream :
            <a class="postlink" href="http://bit.ly/example">Mediafire</a></li></ul>
            <ul><li>Bleach Bankai Revolution 2.0 : Spoiler:
            <a class="postlink" href="https://example.com/bleach.zip">Archive</a></li></ul>
        '''
        with patch('mod_sources.html_page', side_effect=lambda url: (url, markup)):
            result = manager.discover('ultimate')
        self.assertEqual(len(result['pages']), 2)
        self.assertEqual([(item['name'], item['page_url'], item['kind'], item['source_page'])
                          for item in result['projects']], [
            ('Naruto: Battle For Dream', 'https://bit.ly/example', 'external_reference', thread),
            ('Bleach Bankai Revolution 2.0', 'https://example.com/bleach.zip', 'external_reference', thread),
        ])

    def test_duplicate_and_prefix_collision(self):
        for files in ({'A.dat': b'a', 'a.dat': b'b'}, {'a.dat': b'a', 'a.dat/b.dat': b'b'}):
            self.make_zip(files)
            with self.assertRaises(ValueError): archive.inspect_zip(self.zip)

    def test_symlink_and_executable_rejected(self):
        self.make_zip({'setup.exe': b'MZ'})
        with self.assertRaises(ValueError): archive.inspect_zip(self.zip)
        with zipfile.ZipFile(self.zip, 'w') as output:
            info = zipfile.ZipInfo('link.dat'); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            output.writestr(info, '../outside')
        with self.assertRaises(ValueError): archive.inspect_zip(self.zip)

    def test_expansion_limit(self):
        with zipfile.ZipFile(self.zip, 'w', compression=zipfile.ZIP_DEFLATED) as output: output.writestr('large.dat', b'0' * 100000)
        with self.assertRaises(ValueError): archive.inspect_zip(self.zip)

    def test_extraction_and_no_overwrite(self):
        self.make_zip({'folder/a.dat': b'abc'})
        output = self.root / 'output'
        result = archive.extract_zip(self.zip, output)
        self.assertEqual((output / 'folder/a.dat').read_bytes(), b'abc')
        self.assertEqual(len(result['sha256']), 64)
        with self.assertRaises(ValueError): archive.extract_zip(self.zip, output)

    def test_failed_extraction_leaves_no_partial_install(self):
        self.make_zip({'a.dat': b'abc'})
        with patch('zipfile.ZipFile.open', side_effect=OSError('read failed')):
            with self.assertRaises(OSError): archive.extract_zip(self.zip, self.root / 'output')
        self.assertFalse((self.root / 'output').exists())
        self.assertFalse(list(self.root.glob('.mod-staging-*')))

    def test_import_and_failure_cleanup(self):
        files = {'game/data/data.txt': '<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n<background>\n<background_end>',
                 'game/data/hero.dat': encode('<bmp_begin>\nname: Test\n<bmp_end>\n<frame> 0 stand\n<frame_end>', b'x' * 123),
                 'game/data/stage.dat': encode('<stage> id: 0\n<stage_end>', b'x' * 123)}
        self.make_zip(files)
        output = self.root / 'pack'
        result = manager.import_zip(self.zip, output, 'test-mod')
        self.assertTrue((output / 'package.manifest').is_file())
        self.assertFalse(result['active']); self.assertEqual(result['compatibility'], 'not_tested')
        self.assertEqual(result['fighters'][0]['name'], 'Test')
        self.assertEqual(json.loads((output / 'import-report.json').read_text())['archive_sha256'], result['archive_sha256'])
        del files['game/data/hero.dat']; self.make_zip(files)
        with self.assertRaises(ValueError): manager.import_zip(self.zip, self.root / 'failed', 'bad-mod')
        self.assertFalse((self.root / 'failed').exists())
        self.assertFalse(list(self.root.glob('.mod-import-*')))

    def test_android_export_contains_only_verified_converter_package(self):
        files = {'game/data/data.txt': '<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n<background>\n<background_end>',
                 'game/data/hero.dat': encode('<bmp_begin>\nname: Test\nhead: data/head.bmp\n<bmp_end>\n<frame> 0 stand\n<frame_end>', b'x' * 123),
                 'game/data/head.bmp': b'pixel-data',
                 'game/data/stage.dat': encode('<stage> id: 0\n<stage_end>', b'x' * 123)}
        self.make_zip(files)
        home=self.root/'manager';library=Library(home);installed=library.install(self.zip)['package']
        output=self.root/'transfer.lfmod.zip';result=library.export_android(installed['id'],output)
        self.assertTrue(output.is_file());self.assertFalse(result['gameplay_verified'])
        with zipfile.ZipFile(output) as package:
            names=set(package.namelist())
            self.assertIn(installed['id']+'/package.manifest',names)
            self.assertIn(installed['id']+'/catalog.lua',names)
            self.assertIn(installed['id']+'/sounds.lua',names)
            self.assertTrue(any('/assets/' in name for name in names))
        with self.assertRaises(ValueError):library.export_android(installed['id'],output)


if __name__ == '__main__': unittest.main()
