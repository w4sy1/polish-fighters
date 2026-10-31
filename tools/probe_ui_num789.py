"""Stage the updated Lua UI separately and exercise the real Windows executable."""
import json
import shutil
from pathlib import Path
import probe_hub_controls as probe

ROOT=Path(__file__).resolve().parents[1]
probe.PORTABLE=ROOT/'engine/out/LittleFighters-ui-num789-2026-10-31'
probe.OUT=ROOT/'validation/ui-num789-2026-10-31'
if __name__=='__main__':
    if not probe.PORTABLE.exists():
        shutil.copytree(ROOT/'engine/out/LittleFighters-hub-2026-10-31',probe.PORTABLE,
                        ignore=shutil.ignore_patterns('userdata','recordings'))
    shutil.copytree(ROOT/'engine/scripts',probe.PORTABLE/'scripts',dirs_exist_ok=True)
    for name in ['LittleFighters.exe','openlf2.exe']:
        shutil.copy2(ROOT/'engine/build/windows/x64/native/Release/openlf2.exe',probe.PORTABLE/name)
    log,_=probe.run('main','*2',['--hub-menu'],True)
    assert 'hub=true:root' in log
    log,config=probe.run('num789',probe.click(600,212)+','+probe.click(620,160)+','+
                         probe.click(620,371)+','+probe.click(300,495)+',*2',['--hub-menu'],True)
    data=json.loads((config/'config.json').read_text(encoding='utf-8'))
    player=data['controls']['players'][0]
    assert (player['attack'],player['jump'],player['defend'])==(103,104,105),player
    probe.run('controls',probe.click(600,212)+',*2',['--hub-menu'],True,config)
    probe.run('polish-profile',probe.click(220,212)+',*2',['--hub-menu'],True)
    probe.run('selection',probe.click(600,286)+',*2',['--hub-menu'],True)
    (probe.OUT/'summary.json').write_text(json.dumps({'passed':True,'preset':'WASD + Num7/8/9',
        'bindings':player,'captures':['main','num789','controls','polish-profile','selection']},
        ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: native menu, numpad preset saved, control reload, Polish profile and selection; '+str(probe.PORTABLE))
