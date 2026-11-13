"""Native HUD render, Szymonoko clone and checkpoint regressions with real content."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS={
'hud': '''s.launch.hub_enabled=false;s.launch.page='hud'
 local options=require('base/game/options').current();options.touch_layout='modern'
 s.launch.hud=require('base/ui/hud_editor').create(options)''',
'training': '''local catalog=require('base/game/catalog');local fighters=catalog.load();local row
 for n,f in ipairs(fighters) do if f.id==411 then row=n end end
 assert(row)
 s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,training=true,
  fighters=fighters,backgrounds=catalog.backgrounds(),slots={[0]={kind='human',fighter=row,team=1}}})
 s.active='match';s.wait_release=nil
 local m=s.match.match;local heroes=require('polish-originals/heroes');local objects=require('base/game/objects')
 assert(m.items[11] and m.training)
 assert(heroes.clone(m,0,m.items[0],objects))
 local child
 for index,v in pairs(m.items) do if v.pf_clone then child=index end end
 assert(child and not heroes.clone(m,child,m.items[child],objects))
 assert(not heroes.clone(m,0,m.items[0],objects))
 m.items[child].hp=0;assert(heroes.clone(m,0,m.items[0],objects))
 local count=0;for _,v in pairs(m.items) do if v.pf_clone and v.hp>0 then count=count+1 end end
 assert(count==1)
 m.items[11].hp=0
 s.qa_native_clones=true''',
'checkpoint': '''local catalog=require('base/game/catalog');local fighters=catalog.load();local row
 for n,f in ipairs(fighters) do if f.id==411 then row=n end end
 s.match=require('base/ui/match_screen').create({mode=1,difficulty=0,background=0,stage_level=0,
  fighters=fighters,backgrounds=catalog.backgrounds(),slots={[0]={kind='human',fighter=row,team=1}}})
 s.active='match';s.wait_release=nil
 local m=s.match.match;local saves=require('base/game/campaign_save')
 m.stage_run.id=1;m.items[0].hp=321;assert(saves.capture(m))
 m.stage_run.id=2;assert(saves.capture(m))
 local doc=engine.read_settings();local key=doc.campaign_last[catalog.profile_id]
 doc.campaign_checkpoints[key].current.payload.level=59;assert(engine.write_settings(doc))
 local resumed=assert(saves.options(catalog.profile_id));assert(resumed.stage_level==1)
 s.match=require('base/ui/match_screen').create(resumed)
 assert(s.match.match.stage_run.id==1 and s.match.match.items[0].hp==321)
 local doc=engine.read_settings();doc.qa_checkpoint={passed=true,stage=1,hp=321};assert(engine.write_settings(doc))
 s.qa_native_checkpoint=true''',
}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--content-root',type=Path,default=ROOT)
    parser.add_argument('--installer',type=Path)
    parser.add_argument('--scripts',type=Path)
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    ROOT=args.content_root.resolve()
    installer=args.installer.resolve() if args.installer else ROOT.parent/'downloads/LF2_v2.0a.exe'
    scripts=args.scripts.resolve() if args.scripts else ROOT/'engine/scripts'
    results=[]
    for name,body in SCRIPTS.items():
        folder=out/name;folder.mkdir(exist_ok=True)
        (folder/'package.manifest').write_text('id=qa-gameplay-update\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\n'
            'extend=base/ui/flow|flow.lua\n')
        (folder/'flow.lua').write_text('return function(base)\nlocal create,describe=base.create,base.describe\n'
            'function base.create(options) local s=create(options)\n'+body+'\nreturn s end\n'
            'function base.describe(s) return describe(s).." qa_native_clones="..tostring(s.qa_native_clones)..'
            '" qa_native_checkpoint="..tostring(s.qa_native_checkpoint) end\nreturn base end\n')
        command=[str(args.engine.resolve()),'--installer',str(installer),
            '--scripts',str(scripts),'--mod',str(ROOT/'content-packs/polish-originals'),
            '--mod',str(folder),'--config-dir',str(folder/'config'),'--seed','42',
            '--input-trace','*3' if name=='hud' else 'rbc*40','--capture-frame',str(folder/'screen.png')]
        process=subprocess.run(command,capture_output=True,text=True,timeout=90)
        log=process.stdout+process.stderr;(folder/'run.log').write_text(log,encoding='utf-8')
        expected={'hud':'launch_page=hud','training':'qa_native_clones=true','checkpoint':'qa_native_checkpoint=true'}[name]
        passed=process.returncode==0 and expected in log and (folder/'screen.png').is_file()
        results.append({'case':name,'passed':passed,'exit':process.returncode})
        print(results[-1],flush=True)
        if not passed: print(log[-2000:],flush=True)
    (out/'summary.json').write_text(json.dumps(results,indent=2))
    raise SystemExit(0 if all(r['passed'] for r in results) else 1)
