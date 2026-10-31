"""Inventory every imported map/adventure and run isolated native map/stage warmups.
Warmups exercise starts, not campaign completion; never run original executables.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import subprocess
from pathlib import Path
from import_legacy import decode
from read_pinned_lf2 import read_resource
from probe_native_packs import TRACE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'validation/maps-build-2026-10-30'
PACKS=['bleach','kate','reinforced','lf4-turbo','ntsd','dbz','one-piece','lf2-classic']

def inventory(pack):
    if pack=='lf2-classic':
        installer=ROOT/'../downloads/LF2_v2.0a.exe'
        catalog=read_resource(installer,'data/data.txt').decode('latin1').replace('\\','/')
        maps=[{'row':row,'id':int(id_),'resource':path,'missing_resources':[]} for row,(id_,path) in enumerate(re.findall(r'id:\s*(\d+)\s+file:\s*(\S+)',catalog))]
        maps.append({'row':99,'id':99,'key':'builtin-lee-on-road','resource':'builtin/lee-on-road','missing_resources':[]})
        raw=read_resource(installer,'data/stage.dat');text=re.sub(r'#[^\r\n]*','',decode(raw))
        stages=[]
        for block in re.findall(r'<stage>(.*?)<stage_end>',text,re.S):
            id_=re.search(r'\bid:\s*(-?\d+)',block)
            if id_:stages.append({'id':int(id_[1]),'phases':[{'phase':i} for i,_ in enumerate(re.findall(r'<phase>',block))]})
        report={'pack':pack,'maps':maps,'adventures':[{'resource':'data/stage.dat','sha256':hashlib.sha256(raw).hexdigest(),'stages':stages}],
                'static_scope':'Original pinned archive catalog, stage boundaries; native warmups validate actual resource reads. Imported-pack phase field analysis is separate.'}
        OUT.mkdir(parents=True,exist_ok=True);(OUT/(pack+'-inventory.json')).write_text(json.dumps(report,indent=2)+'\n')
        return report
    folder=ROOT/'content-packs'/pack
    assets={v:folder/r for v,r in [line[6:].split('|',1) for line in (folder/'package.manifest').read_text().splitlines() if line.startswith('asset=')]}
    text=next(p for p in assets.values() if p.suffix=='.txt').read_text(encoding='latin1')
    objects={int(i):path for i,path in re.findall(r'id:\s*(\d+)\s+type:\s*\d+\s+file:\s*(\S+)',text)}
    frames={i:set(map(int,re.findall(r'<frame>\s+(\d+)',decode(assets[p].read_bytes())))) for i,p in objects.items() if p in assets and assets[p].exists()}
    maps=[]
    for row,(id_,path) in enumerate(re.findall(r'id:\s*(\d+)\s+file:\s*(\S+)',text)):
        source=re.sub(r'#[^\r\n]*','',decode(assets[path].read_bytes()))
        refs=re.findall(r'\b(?:pic|file):\s*(\S+)',source)
        refs.extend(re.findall(r'\bshadow:\s*(\S+)',source))
        refs=[r for r in refs if '/' in r or '.' in r]
        maps.append({'row':row,'id':int(id_),'resource':path,'layers':len(re.findall(r'\blayer:',source)),
                     'missing_resources':[r for r in refs if r not in assets or not assets[r].exists()]})
    adventures=[]
    for path,p in assets.items():
        if p.suffix!='.dat' or not p.exists():continue
        text=re.sub(r'#[^\r\n]*','',decode(p.read_bytes()))
        if '<stage>' not in text:continue
        stages=[]
        for block in re.findall(r'<stage>(.*?)<stage_end>',text,re.S):
            stage_id=re.search(r'\bid:\s*(-?\d+)',block)
            if not stage_id:continue
            phases=[]
            for number,phase in enumerate(re.findall(r'<phase>(.*?)<phase_end>',block,re.S)):
                entries=[]
                for entry in re.split(r'\bid:\s*',phase)[1:]:
                    fields={key:int(value) for key,value in re.findall(r'\b(act|hp|times|reserve|join|join_reserve|x|y):\s*(-?\d+)',entry)}
                    oid=int(re.match(r'-?\d+',entry)[0]);action=fields.get('act',9)
                    entries.append({'id':oid,'act':action,'missing_object':oid>=0 and oid not in objects and oid not in [1000,3000,3001],
                                    'missing_action':oid in frames and action not in frames[oid],**fields})
                jump=re.search(r'when_clear_goto_phase:\s*(-?\d+)',phase)
                music=re.search(r'\bmusic:\s*(\S+)',phase)
                phases.append({'phase':number,'entries':entries,'jump':int(jump[1]) if jump else -1,
                               'music':music[1] if music else None,
                               'missing_music':bool(music and (music[1] not in assets or not assets[music[1]].exists()))})
            stages.append({'id':int(stage_id[1]),'phases':phases,'outside_native_range':not 0<=int(stage_id[1])<60,
                           'invalid_phase_jumps':[x['phase'] for x in phases if x['jump']>=len(phases)]})
        adventures.append({'resource':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'stages':stages,
                           'unclosed_stages':text.count('<stage>')!=text.count('<stage_end>'),
                           'unclosed_phases':text.count('<phase>')!=text.count('<phase_end>')})
    report={'pack':pack,'maps':maps,'adventures':adventures,'native':[]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(pack+'-inventory.json')).write_text(json.dumps(report,indent=2)+'\n')
    return report

def probe(pack,kind,key,row,stage_path=None,stage_id=None,engine=None,scene_mode=None):
    if pack=='dbz' and stage_path:
        definitions=json.loads((ROOT/'content-packs/dbz/stage-scenes.json').read_text())['stages']
        selected=definitions.get(stage_path,{}).get(str(stage_id))
        if selected:row=selected['row']
    folder=OUT/'native'/pack/(kind+'-'+str(key));folder.mkdir(parents=True,exist_ok=True)
    override=folder/'qa';override.mkdir(exist_ok=True)
    report=json.loads((ROOT/'content-packs'/pack/'import-report.json').read_text()) if pack!='lf2-classic' else {'fighters':[{'id':0}]}
    fighter=50 if pack=='ntsd' else report['fighters'][0]['id']
    requirement='requires='+pack+'@1\n' if pack!='lf2-classic' else ''
    (override/'package.manifest').write_text('id=map-adventure-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\n'+requirement+'replace=polish-fighters/settings|settings.lua\nextend=base/ui/match_screen|probe.lua\n')
    (override/'settings.lua').write_text('return {allowed_ids={'+str(fighter)+'},allow_hidden=true}\n')
    # Separate map/stage diagnosis from unrelated extended fighter parser failures.
    # Only the QA human is stock Deep; campaign enemies remain authored pack records.
    setup='options.background='+str(row)+'\noptions.fighters={{id=0,path="data/deep.dat",name="Deep"}};options.slots={[0]={kind="human",fighter=1,team=1}}\n'
    if scene_mode is not None:setup+='options.scene_mode='+str(scene_mode)+'\n'
    if stage_path:
        setup+='options.mode=1;options.stage_level='+str(stage_id)+';options.campaign_path='+json.dumps(stage_path)+';options.campaign_background='+str(row)+'\n'
    else:setup+='options.mode=0;for slot=1,7 do options.slots[slot]=nil end\n'
    (override/'probe.lua').write_text('''return function(base)
 local create,draw=base.create,base.draw
 local frames=0
 function base.create(options)
 '''+setup+'''
  local state=create(options)
  local doc=engine.read_settings() or {};doc.map_probe={created=true,background=state.match.background_row,qa_actor="data/deep.dat",width=state.match.stage.width,
   scene_mode=state.match.stage.dbz_mode and state.match.stage.dbz_mode.name,
   scene_objects=state.match.dbz_scene_objects and #state.match.dbz_scene_objects};assert(engine.write_settings(doc))
  return state
 end
 function base.draw(state,context,bounds)
  draw(state,context,bounds)
  frames=frames+1
  if frames==120 then
   local doc=engine.read_settings() or {};doc.map_probe.rendered_frames=frames
   doc.map_probe.stage=state.match.stage_run and state.match.stage_run.id or nil
   assert(engine.write_settings(doc))
  end
 end
 return base
end
''')
    command=[str(engine),'--installer',str(ROOT/'../downloads/LF2_v2.0a.exe'),'--scripts',str(ROOT/'engine/scripts'),
             '--mod',str(ROOT/'engine/scripts/polish-fighters'),*(['--mod',str(ROOT/'content-packs'/pack)] if pack!='lf2-classic' else []),'--mod',str(override),
             '--config-dir',str(folder/'config'),'--seed','42','--input-trace',TRACE.rsplit('*300',1)[0]+'*120']
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=45)
        log=result.stdout+result.stderr;code=result.returncode
    except subprocess.TimeoutExpired:log='TIMEOUT';code=-1
    (folder/'native.log').write_text(log,encoding='utf-8')
    config=folder/'config/config.json';proof=json.loads(config.read_text()).get('map_probe',{}) if config.exists() else {}
    passed=code==0 and proof.get('created') and proof.get('rendered_frames')==120 and proof.get('background')==row
    result={'pack':pack,'kind':kind,'key':key,'row':row,'stage_path':stage_path,'stage_id':stage_id,'exit_code':code,'proof':proof,'pass':bool(passed)}
    (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--native',action='store_true');parser.add_argument('--engine',type=Path);parser.add_argument('--pack',choices=PACKS)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
    reports=[inventory(p) for p in ([args.pack] if args.pack else PACKS)]
    for r in reports:print(r['pack'],'maps',len(r['maps']),'adventures',len(r['adventures']),'stages',sum(len(a['stages']) for a in r['adventures']),flush=True)
    if args.native:
        assert args.engine and args.engine.is_file()
        targets=[]
        for r in reports:
            for m in r['maps']:targets.append((r['pack'],'map',m.get('key',m['row']),m['row'],None,None,args.engine.resolve()))
            for a in r['adventures']:
                for stage in a['stages']:
                    # QA chooses a valid physical map; authored campaign mapping is audited separately.
                    row=min(stage['id']//10+1,len(r['maps'])-1)
                    targets.append((r['pack'],'stage',a['resource'].split('/')[-1]+'-'+str(stage['id']),row,a['resource'],stage['id'],args.engine.resolve()))
        rows=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            for result in pool.map(lambda item:probe(*item),targets):
                rows.append(result);print(result['pack'],result['kind'],result['key'],'PASS' if result['pass'] else 'FAIL',flush=True)
        (OUT/'native-summary.json').write_text(json.dumps({'scope':'Each map rendered 120 frames with stock Deep QA actor; adventure stage warmups use authored enemies. Not full fighter/phase/campaign completion. DBZ uses authored scene/mode; other QA maps selected independently of author unlocks.','binary_sha256':hashlib.sha256(args.engine.read_bytes()).hexdigest(),'tests':rows},indent=2)+'\n')
if __name__=='__main__':main()
