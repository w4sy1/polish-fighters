import difflib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('apply_sdl_android_compat', ROOT/'tools/apply_sdl_android_compat.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SDLAndroidPatchTest(unittest.TestCase):
    def fixture(self, root):
        vendor = root/'engine/build/android/sdl-java/org/libsdl/app'
        vendor.mkdir(parents=True)
        patches = root/'tools/patches'
        patches.mkdir(parents=True)
        old = 'class Controller {\n    boolean permissionSafe = false;\n}\n'
        new = old.replace('false', 'true')
        path = 'org/libsdl/app/Controller.java'
        (vendor/'Controller.java').write_text(old)
        (patches/'sdl3-3.4.14-android.patch').write_text(''.join(difflib.unified_diff(
            old.splitlines(True), new.splitlines(True), fromfile='a/'+path, tofile='b/'+path)))
        (patches/'SDLAndroidCompat.java').write_text('class SDLAndroidCompat {}\n')
        return vendor, old, new

    def test_apply_in_non_git_directory_and_reapply_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vendor, old, new = self.fixture(root)
            self.assertFalse(module.apply_compat(root)['already_applied'])
            self.assertEqual((vendor/'Controller.java').read_text(), new)
            self.assertEqual((vendor/'SDLAndroidCompat.java').read_text(), 'class SDLAndroidCompat {}\n')
            self.assertTrue(module.apply_compat(root)['already_applied'])
            self.assertEqual((vendor/'Controller.java').read_text(), new)

    def test_unknown_vendor_context_is_rejected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vendor, old, new = self.fixture(root)
            unexpected = old.replace('false', 'unknown')
            (vendor/'Controller.java').write_text(unexpected)
            with self.assertRaises(RuntimeError):
                module.apply_compat(root)
            self.assertEqual((vendor/'Controller.java').read_text(), unexpected)
            self.assertFalse((vendor/'SDLAndroidCompat.java').exists())


if __name__ == '__main__':
    unittest.main()
