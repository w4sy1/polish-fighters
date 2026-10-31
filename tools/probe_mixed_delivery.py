"""Verify the final local installation, menu profile reload and preserved assets."""
import hashlib
import json
from pathlib import Path
import probe_hub_controls as ui

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'engine/out/LittleFighters-mixed-online-2026-10-31'
OUT=ROOT/'validation/mixed-delivery-2026-10-31'

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    ui.PORTABLE,ui.OUT=STAGE,OUT
    # Actual in-process profile action, rather than preloading mixed-all from CLI.
    arguments=['--hub-menu','--installer',str(STAGE/'LF2_v2.0a.exe')]
    log,_=ui.run('menu-reload',ui.click(200,175)+','+ui.click(600,212)+',*3',arguments,True)
    assert 'mixed-all' in log,log[-1500:]
    log,_=ui.run('extras',ui.click(600,360)+',*3',arguments,True)
    assert 'pf_panel=extras' in log,log[-1500:]
    assets=0
    for pack in (STAGE/'content-packs').iterdir():
        if not (pack/'package.manifest').is_file():continue
        source=ROOT/'content-packs'/pack.name
        assert digest(pack/'package.manifest')==digest(source/'package.manifest'),pack.name
        for path in source.glob('*.lua'):
            assert digest(path)==digest(pack/path.name),str(path)
        for line in (pack/'package.manifest').read_text().splitlines():
            if not line.startswith('asset='):continue
            _,relative=line[6:].split('|',1)
            assert digest(pack/relative)==digest(source/relative),relative
            assets+=1
    for path in (ROOT/'engine/scripts').rglob('*'):
        if path.is_file():assert digest(path)==digest(STAGE/'scripts'/path.relative_to(ROOT/'engine/scripts')),str(path)
    assert digest(STAGE/'LittleFighters.exe')==digest(ROOT/'engine/build/windows/x64/native/Release/openlf2.exe')
    # The recovery baseline predates intentional source-code changes; only original
    # imported resource data is protected byte-for-byte by this check.
    baseline=json.loads((ROOT/'validation/polish-originals-2026-10-30/preservation-before.json').read_text())
    protected={name:value for name,value in baseline.items() if '/assets/' in name}
    for name,value in protected.items():assert digest(ROOT/name)==value,name
    result={'pass':True,'menu_profile_reload':True,'extras_rendered':True,
            'staged_asset_hashes':assets,'original_asset_hashes_preserved':len(protected)}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
