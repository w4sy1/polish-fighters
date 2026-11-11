"""Verify preservation, data links, hashes, manifest assets and idempotent generation."""
import hashlib
import json
import re
from pathlib import Path
from import_legacy import decode
from build_remonoko import build, ROOT, PACK

OUT = ROOT / 'validation/remonoko-2026-11-06'


def digest(path):
    path = Path(path)
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    protected = json.loads((ROOT / 'validation/polish-originals-2026-10-30/preservation-before.json').read_text())
    protected = {name: sha for name, sha in protected.items() if '/assets/' in name}
    for name, sha in protected.items():
        assert digest(ROOT / name) == sha, name
    before = OUT / 'before/polish-originals'
    unchanged = 0
    for old in (before / 'assets').glob('*'):
        if old.name == 'catalog.txt' or not old.is_file():
            continue
        assert digest(old) == digest(PACK / 'assets' / old.name), old.name
        unchanged += 1
    for old in (before / 'art').glob('*.png'):
        assert digest(old) == digest(PACK / 'art' / old.name), old.name
        unchanged += 1
    for path, original in ((PACK / 'assets/catalog.txt', before / 'assets/catalog.txt'),
                           (ROOT / 'content-packs/mixed-all/assets/catalog.txt', OUT / 'before/mixed-assets-catalog.txt')):
        text = path.read_text(encoding='latin1')
        without = re.sub(r'^id:\s*(?:414|415|427|428|429|43[0-9])\s+type:[^\n]*\n', '', text, flags=re.M)
        assert without == original.read_text(encoding='latin1'), path
        ids = re.findall(r'^id:\s*(\d+)\s+type:', text, re.M)
        assert len(ids) == len(set(ids)), 'duplicate object IDs'
    frames = 0
    for name in ('r', 'm', '427', '428', '429', *map(str, range(430,440))):
        text = decode((PACK / f'assets/{name}.dat').read_bytes())
        assert 'sound:' not in text, 'unexpected voice/sound inherited into RN DAT'
        matches = list(re.finditer(r'<frame>\s*(\d+)\s+(.*?)<frame_end>', text, re.S))
        numbers = {int(m[1]) for m in matches}
        assert len(numbers) == len(matches)
        for match in matches:
            assert 0 <= int(re.search(r'pic:\s*(\d+)', match[2])[1]) < 64
            for m in re.finditer(r'\b(?:next|hit_[FUD][aj]|hit_ja):\s*(-?\d+)', match[2]):
                assert abs(int(m[1])) in numbers | {0, 999, 1000}, (name, match[1], m[1])
        frames += len(matches)
    hashes = json.loads((PACK / 'asset-checksums.json').read_text())
    for name, sha in hashes.items():
        assert digest(PACK / name) == sha, name
    for line in (PACK / 'package.manifest').read_text().splitlines():
        if line.startswith('asset='):
            virtual, relative = line[6:].split('|', 1)
            assert (PACK / relative).is_file(), relative
            assert len(virtual) < 40, virtual
    paths = list(PACK.glob('*.json')) + list(PACK.glob('*.lua')) + [PACK / 'package.manifest'] + list((PACK / 'assets').glob('*'))
    generated_before = {str(p): digest(p) for p in paths if p.is_file()}
    build()
    assert all(digest(p) == sha for p, sha in generated_before.items()), 'builder is not idempotent'
    report = dict(pass_=True, original_imported_assets=len(protected), previous_own_assets=unchanged,
                  new_dat_frames=frames, asset_hashes=len(hashes), catalogs_preserved=True,
                  builder_idempotent=True, no_RN_sounds=True)
    (OUT / 'asset-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
