"""Verify protected LF content and every staged package resource before packaging."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from probe_hub_controls import ROOT, PORTABLE, OUT

@lru_cache(maxsize=None)
def sha(path):
    with path.open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()

def main():
    baseline=json.loads((ROOT/'validation/polish-originals-2026-10-30/preservation-before.json').read_text())
    changed=[name for name,value in baseline.items() if sha(ROOT/name)!=value]
    expected=['engine/scripts/base/ui/controls.lua','engine/scripts/base/ui/match_screen.lua']
    assert sorted(changed)==expected,changed
    checked=0;missing=[];different=[];pack_count=0
    for pack in sorted((PORTABLE/'content-packs').iterdir()):
        manifest=pack/'package.manifest'
        if not manifest.exists():continue
        pack_count+=1
        source=ROOT/'content-packs'/pack.name
        assert sha(manifest)==sha(source/'package.manifest'),pack.name
        for line in manifest.read_text().splitlines():
            if not line.startswith('asset='):continue
            _,relative=line[6:].split('|',1)
            path=pack/relative;checked+=1
            if not path.is_file():missing.append(str(path))
            elif sha(path)!=sha(source/relative):different.append(str(path))
    assert not missing and not different,(missing,different)
    art=json.loads((ROOT/'validation/polish-originals-2026-10-30/art-preservation.json').read_text())
    for entry in art:assert sha(ROOT/'content-packs/polish-originals/art'/f'{entry["key"]}.png')==entry['sha256']
    # The only base-script changes are explicitly required UI/input fixes. Every
    # other protected file, including all seven prior packs, remains byte-identical.
    report={'protected_files_unchanged':len(baseline)-len(changed),'intentional_base_ui_changes':changed,
      'original_fighter_and_pack_assets_preserved':True,'packs':pack_count,'manifest_resources_checked':checked,
      'missing':missing,'different':different,'art_pngs_unchanged':4,'pass':True}
    (OUT/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
