#!/usr/bin/env python3
"""Convert one legacy LF2 data folder into an isolated OpenLF2 package.
Keeps original IDs; does not merge packs, execute EXEs or emulate EXE patches.
"""
import argparse,hashlib,json,re,shutil
from pathlib import Path,PurePosixPath
KEY=b'SiuHungIsAGoodBearBecauseHeIsVeryGood'
RESOURCE=re.compile(r'(?i)([a-z0-9_./\\-]+\.(?:bmp|png|wav|dat|wma|mp3|ogg))')
ROOT=Path(__file__).resolve().parents[1]
def decode(data):
 if len(data)<123:raise ValueError('Truncated encrypted LF2 data')
 return bytes((b-KEY[i%len(KEY)])%256 for i,b in enumerate(data[123:],123)).decode('latin1')
def encode(text,header):
 return header[:123]+bytes((b+KEY[i%len(KEY)])%256 for i,b in enumerate(text.encode('latin1'),123))
def canonical(value):
 value=value.replace('\\','/').lower();p=PurePosixPath(value)
 if p.is_absolute() or '..' in p.parts or ':' in value or not re.fullmatch(r'[a-z0-9_./-]+',value):raise ValueError('Unsafe resource path: '+value)
 return p.as_posix()

def convert(source,destination,pack_id,png_aliases=False,catalog_markers=(),allow_missing=False):
 source=Path(source).resolve(strict=True);destination=Path(destination).resolve()
 if destination.exists():raise ValueError('Destination already exists; choose a new directory')
 if source==destination or source in destination.parents:raise ValueError('Destination must be outside source')
 if not re.fullmatch(r'[a-z][a-z0-9-]{1,40}',pack_id):raise ValueError('Invalid package ID')
 files={}
 for path in source.rglob('*'):
  if path.is_symlink():continue
  if path.is_file():
   relative=canonical(path.relative_to(source).as_posix()) if re.fullmatch(r'[A-Za-z0-9_./\\-]+',path.relative_to(source).as_posix()) else None
   if relative:
    if relative in files:raise ValueError('Case-colliding resource: '+relative)
    files[relative]=path
 catalog=files['data/data.txt'].read_text(encoding='latin1')
 objects=re.search(r'<object>(.*?)<object_end>',catalog,re.S).group(1)
 backgrounds=re.search(r'<background>(.*?)<background_end>',catalog,re.S).group(1)
 records=[];bgs=[];seen=set();markers=[];aliases={};custom_labels=[]
 for raw in objects.splitlines():
  line=raw.split('#',1)[0].strip()
  if not line:continue
  if line in catalog_markers:
   markers.append(line);continue
  if catalog_markers and 'fileb:' in line:
   custom_labels.append(line);line=line.replace('fileb:','file:')
  m=re.fullmatch(r'id:\s*(\d+)\s+type:\s*(\d+)\s+file:\s*(\S+)',line)
  if not m:raise ValueError('Unsupported object catalog line: '+line)
  id_,kind,path=m.groups();id_=int(id_)
  if id_ in seen:raise ValueError('Duplicate object ID: '+str(id_))
  seen.add(id_);records.append((id_,int(kind),canonical(path)))
 for raw in backgrounds.splitlines():
  line=raw.split('#',1)[0].strip()
  if not line:continue
  m=re.fullmatch(r'id:\s*(\d+)\s+file:\s*(\S+)',line)
  if not m:raise ValueError('Unsupported background line: '+line)
  bgs.append((int(m[1]),canonical(m[2])))
 prefix='mods/'+pack_id+'/'
 mapping={}
 def resolve(path):
  path=canonical(path)
  if path not in files and png_aliases and path.endswith('.bmp') and path[:-4]+'.png' in files:
   aliases[path]=path[:-4]+'.png';return aliases[path]
  return path
 def register(path):
  path=resolve(path)
  if path not in mapping:mapping[path]=f'a/{len(mapping):06d}'+Path(path).suffix
  return prefix+mapping[path]
 queue=[p for _,_,p in records]+[p for _,p in bgs]+['data/stage.dat']
 # Copy fixed/menu sounds too, so legacy menu/combat audio can be redirected.
 queue += [p for p in files if re.fullmatch(r'data/(?:\d{3}|m_[a-z]+)\.wav',p)]
 converted={};missing=set();fighters=[];disabled_sounds=[]
 while queue:
  path=resolve(queue.pop())
  if path in converted or path in missing:continue
  if path not in files:missing.add(path);continue
  raw=files[path].read_bytes()
  if path.endswith('.dat'):
   text=decode(raw)
   def replace(match):
    # The native frame reader recognizes the exact token sound:, not #sound:.
    # Keep disabled author annotations without inventing an asset dependency.
    line_prefix=text[text.rfind('\n',0,match.start())+1:match.start()]
    if re.fullmatch(r'\s*#sound:\s*',line_prefix):
     disabled_sounds.append({'source':path,'resource':canonical(match[1])})
     return match[0]
    resource=canonical(match[1]);queue.append(resource);return register(resource)
   # Frame labels are cosmetic, but the native reader retains the original 19-byte bound.
   text=re.sub(r'(?m)(<frame>\s+\d+\s+)(\S+)',lambda m:m[1]+m[2][:19],text)
   text=RESOURCE.sub(replace,text)
   converted[path]=encode(text,raw)
  else:converted[path]=raw
 if missing and not allow_missing:raise ValueError('Missing referenced resources: '+', '.join(sorted(missing)))
 for id_,kind,path in records:
  if kind==0:
   if path not in files:
    fighters.append({'id':id_,'name':'[missing]','path':path});continue
   text=decode(files[path].read_bytes());name=re.search(r'\bname:\s*(\S+)',text)
   fighters.append({'id':id_,'name':name[1] if name else '?','path':path})
 # All failures above leave no partially installed destination.
 destination.mkdir(parents=True)
 try:
  for path,data in converted.items():
   register(path)
   out=destination/'assets'/mapping[path];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
  lines=['<object>']+[f'id: {id_} type: {kind} file: {register(path)}' for id_,kind,path in records]+['<object_end>','<background>']+[f'id: {id_} file: {register(path)}' for id_,path in bgs]+['<background_end>']
  register('data/data.txt')
  (destination/'assets'/mapping['data/data.txt']).write_text('\n'.join(lines)+'\n')
  converted['data/data.txt']=b''
  manifest=f'id={pack_id}\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nextend=base/game/catalog|catalog.lua\nextend=base/game/sounds|sounds.lua\n'
  manifest+=''.join(f'asset={register(p)}|assets/{mapping[p]}\n' for p in sorted(converted))
  if len(manifest.encode())>262144:raise ValueError('Package manifest exceeds engine limit')
  (destination/'package.manifest').write_text(manifest)
  campaigns=[]
  if 'data/stage.dat' in files:
   for block in re.findall(r'<stage_information>(.*?)<stage_information_end>',decode(files['data/stage.dat'].read_bytes()),re.S):
    fields={k:v for k,v in re.findall(r'\b(id|name|file):\s*(\S+)',block)}
    if not all(k in fields for k in ('id','name','file')):continue
    path=canonical(fields['file'])
    if path not in converted:continue
    text=decode(files[path].read_bytes());start=re.search(r'<stage>\s*id:\s*(\d+)',text)
    bg=re.search(r'\bbg:\s*(\d+)',text)
    row=next((i for i,(id_,_) in enumerate(bgs) if bg and id_==int(bg[1])),None)
    hidden=re.search(r'\bhidden:\s*(-?\d+)',block)
    campaigns.append({'id':int(fields['id']),'name':fields['name'],'path':register(path),'start_id':int(start[1]) if start else 0,'background':row,'requires_custom_unlock':bool(hidden)})
  campaign_lua='\n base.campaigns={\n'
  for c in campaigns:
   campaign_lua+=' {id='+str(c['id'])+',name='+json.dumps(c['name'],ensure_ascii=False)+',path='+json.dumps(c['path'])+',start_id='+str(c['start_id'])+((',background='+str(c['background'])) if c['background'] is not None else '')+',requires_custom_unlock='+str(c['requires_custom_unlock']).lower()+'},\n'
  campaign_lua+=' }\n' if campaigns else ''
  if not campaigns:campaign_lua=''
  (destination/'catalog.lua').write_text('return function(base)\n base.source_path="'+register('data/data.txt')+'"\n base.stage_path="'+register('data/stage.dat')+'"\n base.profile_id="'+pack_id+'"'+campaign_lua+'\n return base\nend\n')
  sound_paths={p:register(p) for p in converted if p.endswith('.wav')}
  (destination/'sounds.lua').write_text('return function(base)\n local paths={\n'+''.join(' ["'+k+'"]="'+v+'",\n' for k,v in sorted(sound_paths.items()))+' }\n for k,v in pairs(base.fixed_files) do base.fixed_files[k]=paths[v] or v end\n for k,v in pairs(base.menu) do base.menu[k]=paths[v] or v end\n return base\nend\n')
  report={'pack_id':pack_id,'fighters':fighters,'objects':len(records),'backgrounds':len(bgs),'assets':len(converted),'source_catalog_sha256':hashlib.sha256(catalog.encode('latin1')).hexdigest(),'mode':'isolated, original IDs retained','executable_patches_emulated':False,'gameplay_verified':False,'png_aliases':aliases,'catalog_markers_not_emulated':markers,'custom_catalog_labels':custom_labels,'missing_resources':sorted(missing),'experimental':True}
  report['campaigns']=campaigns
  report['disabled_sound_annotations']=disabled_sounds
  repairs=repair_sprite_edges(destination)
  report['sprite_edge_repairs']=len(repairs['padded'])
  report['unresolved_sprite_sheets']=len(repairs['unresolved'])
  (destination/'import-report.json').write_text(json.dumps(report,indent=2)+'\n')
  return report
 except BaseException:
  shutil.rmtree(destination);raise

def repair_sprite_edges(package):
 from PIL import Image
 package=Path(package);assets={}
 for line in (package/'package.manifest').read_text().splitlines():
  if line.startswith('asset='):
   virtual,local=line[6:].split('|');assets[virtual]=package/local
 required={}
 pattern=re.compile(r'file\([^)]*\):\s*(\S+)\s+w:\s*(\d+)\s+h:\s*(\d+)\s+row:\s*(\d+)\s+col:\s*(\d+)')
 for path in assets.values():
  if path.suffix=='.dat':
   for match in pattern.finditer(decode(path.read_bytes())):
    name,w,h,columns,rows=match.groups()
    size=((int(w)+1)*int(columns)-1,(int(h)+1)*int(rows)-1)
    previous=required.get(name,(0,0));required[name]=(max(previous[0],size[0]),max(previous[1],size[1]))
 padded=[];unresolved=[]
 for name,(width,height) in required.items():
  if name not in assets:
   unresolved.append({'asset':name,'missing':True});continue
  path=assets[name]
  with Image.open(path) as image:
   dx=max(0,width-image.width);dy=max(0,height-image.height)
   if not(dx or dy):continue
   if dx>2 or dy>2:
    unresolved.append({'asset':name,'actual':list(image.size),'required':[width,height]});continue
   before=list(image.size)
   mode='RGBA' if path.suffix=='.png' else 'RGB'
   canvas=Image.new(mode,(max(image.width,width),max(image.height,height)),(0,0,0,0) if mode=='RGBA' else (0,0,0));canvas.paste(image.convert(mode),(0,0))
  canvas.save(path,format='PNG' if path.suffix=='.png' else 'BMP');padded.append({'asset':name,'before':before,'after':list(canvas.size)})
 report={'padded':padded,'unresolved':unresolved}
 (package/'sprite-edge-repairs.json').write_text(json.dumps(report,indent=2)+'\n')
 return report


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('destination');p.add_argument('--id',required=True);p.add_argument('--png-aliases',action='store_true');p.add_argument('--catalog-markers',action='store_true');p.add_argument('--allow-missing',action='store_true',help='Stage experimental data with an explicit missing-resource report');a=p.parse_args()
 try:
  r=convert(a.source,a.destination,a.id,a.png_aliases,('%','$','&','*') if a.catalog_markers else (),a.allow_missing);print(json.dumps(r,indent=2))
 except (ValueError,OSError,KeyError,AttributeError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
