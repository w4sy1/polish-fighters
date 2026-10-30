import importlib.util,unittest,tempfile,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('legacy',Path(__file__).resolve().parents[1]/'tools/import_legacy.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
class ImportTests(unittest.TestCase):
 def test_disabled_sound_annotation_is_not_a_dependency(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';(source/'data').mkdir(parents=True)
   (source/'data/data.txt').write_text('<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n<background>\n<background_end>')
   text='<bmp_begin>\nname: Hero\n<bmp_end>\n<frame> 0 stand\n#sound: data/disabled.wav\n<frame_end>'
   (source/'data/hero.dat').write_bytes(legacy.encode(text,b'x'*123))
   (source/'data/stage.dat').write_bytes(legacy.encode('<stage> id: 0\n<stage_end>',b'x'*123))
   report=legacy.convert(source,root/'pack','test-pack')
   self.assertFalse(report['missing_resources'])
   self.assertEqual(report['disabled_sound_annotations'],[{'source':'data/hero.dat','resource':'data/disabled.wav'}])
   (source/'data/hero.dat').write_bytes(legacy.encode(text.replace('#sound:','sound:'),b'x'*123))
   with self.assertRaises(ValueError):legacy.convert(source,root/'active-pack','test-pack')
 def test_xor_round_trip(self):
  text='<bmp_begin>\nname: Test\n<bmp_end>\n';header=b'x'*123
  self.assertEqual(legacy.decode(legacy.encode(text,header)),text)
 def test_unsafe_path_rejected(self):
  for path in ['../x.dat','C:/x.dat','/etc/passwd']:
   with self.assertRaises(ValueError):legacy.canonical(path)
 def test_repeated_separators_normalized(self):
  self.assertEqual(legacy.canonical('C/GOG//haaaa.wav'),'c/gog/haaaa.wav')
 def test_png_alias_preserves_alpha_and_format(self):
  from PIL import Image
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';(source/'data').mkdir(parents=True);(source/'sprite').mkdir()
   (source/'data/data.txt').write_text('<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n<background>\nid: 0 file: data/bg.dat\n<background_end>')
   texts={'data/hero.dat':'<bmp_begin>\nname: Hero\nhead: sprite/hero.bmp\nfile(0-3): sprite/hero.bmp w: 1 h: 1 row: 2 col: 2\n<bmp_end>\n<frame> 0 stand\n<frame_end>', 'data/bg.dat':'name: Arena\n','data/stage.dat':'<stage> id: 0\n<stage_end>'}
   for name,text in texts.items():(source/name).write_bytes(legacy.encode(text,b'x'*123))
   Image.new('RGBA',(2,2),(200,40,30,128)).save(source/'sprite/hero.png')
   out=root/'pack';report=legacy.convert(source,out,'test-pack',png_aliases=True)
   self.assertEqual(report['png_aliases'],{'sprite/hero.bmp':'sprite/hero.png'})
   image_path=next((out/'assets').rglob('*.png'))
   with Image.open(image_path) as image:
    self.assertEqual(image.format,'PNG');self.assertEqual(image.getpixel((0,0))[3],128)
    self.assertEqual(image.getpixel((2,2))[3],0)
 def test_missing_assets_staged_only_explicitly(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';(source/'data').mkdir(parents=True)
   (source/'data/data.txt').write_text('<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n<background>\n<background_end>')
   (source/'data/hero.dat').write_bytes(legacy.encode('<bmp_begin>\nname: Hero\nhead: missing.bmp\n<bmp_end>',b'x'*123))
   report=legacy.convert(source,root/'pack','test-pack',allow_missing=True)
   self.assertIn('missing.bmp',report['missing_resources']);self.assertTrue(report['experimental'])
 def test_atomic_missing_resource(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';(source/'data').mkdir(parents=True)
   (source/'data/data.txt').write_text('<object>\nid: 1 type: 0 file: data/missing.dat\n<object_end>\n<background>\n<background_end>')
   with self.assertRaises(ValueError):legacy.convert(source,root/'out','test-pack')
   self.assertFalse((root/'out').exists())
 def test_namespace_and_frame_labels(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);source=root/'source';(source/'data').mkdir(parents=True);(source/'sprite').mkdir()
   (source/'data/data.txt').write_text('<object>\nid: 1 type: 0 file: data/hero.dat\n<object_end>\n<background>\nid: 0 file: data/bg.dat\n<background_end>')
   files={'data/hero.dat':'<bmp_begin>\nname: Hero\nhead: sprite/hero.bmp\n<bmp_end>\n<frame> 0 '+('x'*40)+'\n<frame_end>','data/bg.dat':'name: Arena\n','data/stage.dat':'<stage> 0\n<stage_end>'}
   for path,text in files.items():(source/path).write_bytes(legacy.encode(text,b'x'*123))
   (source/'sprite/hero.bmp').write_bytes(b'BM-synthetic')
   out=root/'pack';r=legacy.convert(source,out,'test-pack');self.assertEqual(r['fighters'][0]['name'],'Hero')
   cat=(out/'catalog.lua').read_text();self.assertIn('/a/',cat)
   data='\n'.join(legacy.decode(p.read_bytes()) for p in (out/'assets').rglob('*.dat'))
   self.assertIn('mods/test-pack/a/',data);self.assertNotIn('x'*20,data)
   with self.assertRaises(ValueError):legacy.convert(source,out,'test-pack')
if __name__=='__main__':unittest.main()
