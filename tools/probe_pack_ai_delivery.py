"""Bounded native checks for the pack chooser, character AI and local TCP sync."""
import json
import shutil
from pathlib import Path
import probe_hub_controls as ui
import probe_native_packs as combat
import check_room_game as room

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'engine/out/LittleFighters-pack-ai-2026-10-31'
OUT=ROOT/'validation/pack-ai-2026-10-31'
if __name__=='__main__':
    if not STAGE.exists():
        shutil.copytree(ROOT/'engine/out/LittleFighters-ui-num789-2026-10-31',STAGE,
                        ignore=shutil.ignore_patterns('userdata','recordings'))
    shutil.copytree(ROOT/'engine/scripts',STAGE/'scripts',dirs_exist_ok=True)
    shutil.copytree(ROOT/'content-packs/polish-originals',STAGE/'content-packs/polish-originals',dirs_exist_ok=True)
    ui.PORTABLE,ui.OUT=STAGE,OUT
    # Root -> library -> chooser (first item in second column) -> disable Bleach -> save.
    trace=ui.click(200,175)+','+ui.click(600,175)+','+ui.click(200,470)+','+ui.click(600,212)+',*2'
    log,config=ui.run('pack-save',trace,['--hub-menu'],True)
    selected=json.loads((config/'config.json').read_text())['little_fighters_packs']
    assert selected['bleach'] is False and selected['polish_fighters']
    ui.run('pack-reload','*2',['--hub-menu'],True,config)
    ui.run('selection-pl',ui.click(600,286)+',*8',['--hub-menu'],True)
    fights=[]
    for fighter in range(410,414):
        result=combat.probe('polish-originals',fighter,OUT/'fights',runs=2,geometry=True,combat=True,
            binary=STAGE/'LittleFighters.exe',scripts=STAGE/'scripts',content_root=STAGE/'content-packs')
        fights.append(result)
    assert all(value['pass'] for value in fights),fights
    config_file=ROOT/'tools/room-check/config.lua';original=config_file.read_bytes()
    try:
        network=[room.case(STAGE/'LittleFighters.exe',STAGE/'LF2_v2.0a.exe',4,
                          pack='polish-originals',output_dir=OUT/'network',own=True)]
    finally:config_file.write_bytes(original)
    assert all(value['passed'] for value in network),network
    (OUT/'summary.json').write_text(json.dumps({'pack_selection':True,'fights':fights,'network':network},indent=2))
    print('PASS: package selection persists, native fights repeated and four own fighters TCP sync')
