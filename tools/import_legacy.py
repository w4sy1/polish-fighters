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
def decode_ce_lf2(data):
 # This edition marks a distinct 160-byte header and a repeating 37-byte additive key.
 marker=b'This data file was locked by RaMMicHaeL for Combined Effort Little Fighter 2 mod by Marshall'
 if not data.startswith(marker):
  return decode(data)
 if len(data)<=160:
  raise ValueError('Truncated CE LF2 data')
 key=bytes.fromhex('2f6c6e6161607b2f6d6a2f7d7a612f66612f4b405c2f62606b5b67667c2f7f7d60687d6e62')
 return bytes((byte-key[i%len(key)])%256 for i,byte in enumerate(data[160:])).decode('latin1')

def encode(text,header):
 return header[:123]+bytes((b+KEY[i%len(KEY)])%256 for i,b in enumerate(text.encode('latin1'),123))
def canonical(value):
 value=value.replace('\\','/').lower();p=PurePosixPath(value)
 if p.is_absolute() or '..' in p.parts or ':' in value or not re.fullmatch(r'[a-z0-9_./-]+',value):raise ValueError('Unsafe resource path: '+value)
 return p.as_posix()

# Match the original catalogue before resolving known conflicting IDs.
CATALOG_ID_REPAIRS={
 'lf-seed':('77a0f7fb78957e34acb7c802918d9e8720149ece52236bb9787560ac6b0d547b',
            7,19,'data/strikered.dat'),
 'lf2-sv':('7debc748b99a4a2406e735d129cc83c5fc18d9bb4481b2b5f0a9a616c465d11d',
           150,198,'data/weapon1_broken.dat'),
 'ce-lf2':('1558581a2ff137f5f4b5476f862b6b950cd455806f33308cbd88388a5d68c828',
           199,198,'data/weapon4.dat'),
 'rn-lf2':('bd273c4f71f0b5c2a5bc2c57c2330ffec10178e37f083fb71feb3cbc84a48d9f',
           9,17,'data/dennis.dat'),
}

def convert(source,destination,pack_id,png_aliases=False,catalog_markers=(),allow_missing=False,managed_import=False):
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
 catalog_path='data/data.txt'
 if pack_id=='killer-lf2' and catalog_path not in files:
  catalog_path='data/dat.noes.bak'
 catalog_bytes=files[catalog_path].read_bytes()
 catalog=catalog_bytes.decode('latin1').replace('\r\n','\n').replace('\r','\n')
 catalog_sha256=hashlib.sha256(catalog.encode('latin1')).hexdigest()
 source_hash=hashlib.sha256(catalog_bytes).hexdigest()
 killer=pack_id=='killer-lf2' and source_hash=='fc0ac2c8da23df91e83c20ce82981a51cb6cdfbe585cba53144175da79e20c46'
 if catalog_path!='data/data.txt' and not killer:raise ValueError('Unknown Killer LF2 backup catalogue')
 no_campaign=killer and 'data/stage.dat' not in files
 if killer:from normalize_ntsd_vc80 import FIELD,normalize
 repair=CATALOG_ID_REPAIRS.get(pack_id)
 if repair and source_hash!=repair[0]:repair=None
 source_decode=decode_ce_lf2 if repair and pack_id=='ce-lf2' else decode
 strip_seed_notes=repair is not None and pack_id=='lf-seed'
 id_repair=None
 normalization=None
 normalized_files=[]
 killer_repairs=[]
 if managed_import:
  from normalize_ntsd_vc80 import import_profile, normalize
  normalization=import_profile(source_hash,files)
 objects=re.search(r'<object>(.*?)<object_end>',catalog,re.S).group(1)
 backgrounds=re.search(r'<background>(.*?)<background_end>',catalog,re.S).group(1)
 records=[];bgs=[];seen=set();markers=[];aliases={};custom_labels=[]
 for raw in objects.splitlines():
  line=raw.split('#',1)[0].strip()
  if strip_seed_notes:line=line.split('<-',1)[0].rstrip()
  if not line:continue
  if line in catalog_markers:
   markers.append(line);continue
  if catalog_markers and 'fileb:' in line:
   custom_labels.append(line);line=line.replace('fileb:','file:')
  m=re.fullmatch(r'id:\s*(\d+)\s+type:\s*(\d+)\s+file:\s*(\S+)',line)
  if not m:raise ValueError('Unsupported object catalog line: '+line)
  id_,kind,path=m.groups();id_=int(id_);path=canonical(path)
  if repair and id_==repair[1] and path==repair[3]:
   id_repair={'path':path,'old_id':id_,'new_id':repair[2]}
   id_=repair[2]
  if id_ in seen:raise ValueError('Duplicate object ID: '+str(id_))
  seen.add(id_);records.append((id_,int(kind),path))
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
 queue=[p for _,_,p in records]+[p for _,p in bgs]
 if not no_campaign:queue.append('data/stage.dat')
 # Copy fixed/menu sounds too, so legacy menu/combat audio can be redirected.
 queue += [p for p in files if re.fullmatch(r'data/(?:\d{3}|m_[a-z]+)\.wav',p)]
 converted={};missing=set();fighters=[];disabled_sounds=[]
 while queue:
  path=resolve(queue.pop())
  if path in converted or path in missing:continue
  if path not in files:missing.add(path);continue
  raw=files[path].read_bytes()
  if path.endswith('.dat'):
   text=source_decode(raw)
   if normalization and path in normalization[1]:
    if hashlib.sha256(raw).hexdigest()!=normalization[1][path]:
     raise ValueError('NTSD source DAT changed during import: '+path)
    text,fields=normalize(text,normalization[2])
    normalized_files.append({'path':path,'fields_changed':len(fields)})
   if killer:
    # killer.exe's static %d scanner accumulates and stores the low 32 bits.
    values={field[2]:(int(field[2])+2**31)%2**32-2**31 for field in FIELD.finditer(text)
            if not -2**31<=int(field[2])<2**31}
    text,fields=normalize(text,values)
    if fields:killer_repairs.append({'path':path,'fields':fields})
   def replace(match):
    # The native frame reader recognizes the exact token sound:, not #sound:.
    # Keep disabled author annotations without inventing an asset dependency.
    line_prefix=text[text.rfind('\n',0,match.start())+1:match.start()]
    if re.fullmatch(r'\s*#sound:\s*',line_prefix):
     disabled_sounds.append({'source':path,'resource':canonical(match[1])})
     return match[0]
    resource=canonical(match[1]);queue.append(resource)
    virtual=register(resource)
    # Legacy image fields accept as few as 29 characters. Keep the full
    # namespace in the manifest and resolve these local references on read.
    if managed_import and resource.endswith(('.bmp','.png')):
     return './'+virtual[len(prefix):]
    return virtual
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
   text=source_decode(files[path].read_bytes());name=re.search(r'\bname:\s*(\S+)',text)
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
  if pack_id in {'sx2','ntsd-community','ntsd-ce-setup'}:
   manifest+='extend=base/game/constants|constants.lua\n'
   (destination/'constants.lua').write_text('return function(base)\n base.frame_limit=999\n return base\nend\n')
  manifest+=''.join(f'asset={register(p)}|assets/{mapping[p]}\n' for p in sorted(converted))
  if len(manifest.encode())>262144:raise ValueError('Package manifest exceeds engine limit')
  (destination/'package.manifest').write_text(manifest)
  campaigns=[]
  if 'data/stage.dat' in files:
   for block in re.findall(r'<stage_information>(.*?)<stage_information_end>',source_decode(files['data/stage.dat'].read_bytes()),re.S):
    fields={k:v for k,v in re.findall(r'\b(id|name|file):\s*(\S+)',block)}
    if not all(k in fields for k in ('id','name','file')):continue
    path=canonical(fields['file'])
    if path not in converted:continue
    text=source_decode(files[path].read_bytes());start=re.search(r'<stage>\s*id:\s*(\d+)',text)
    bg=re.search(r'\bbg:\s*(\d+)',text)
    row=next((i for i,(id_,_) in enumerate(bgs) if bg and id_==int(bg[1])),None)
    hidden=re.search(r'\bhidden:\s*(-?\d+)',block)
    campaigns.append({'id':int(fields['id']),'name':fields['name'],'path':register(path),'start_id':int(start[1]) if start else 0,'background':row,'requires_custom_unlock':bool(hidden)})
  campaign_lua='\n base.campaigns={\n'
  for c in campaigns:
   campaign_lua+=' {id='+str(c['id'])+',name='+json.dumps(c['name'],ensure_ascii=False)+',path='+json.dumps(c['path'])+',start_id='+str(c['start_id'])+((',background='+str(c['background'])) if c['background'] is not None else '')+',requires_custom_unlock='+str(c['requires_custom_unlock']).lower()+'},\n'
  campaign_lua+=' }\n' if campaigns else ''
  if not campaigns:campaign_lua='\n base.campaigns={}' if no_campaign else ''
  stage_path='false' if no_campaign else json.dumps(register('data/stage.dat'))
  (destination/'catalog.lua').write_text('return function(base)\n base.source_path="'+register('data/data.txt')+'"\n base.stage_path='+stage_path+'\n base.profile_id="'+pack_id+'"'+campaign_lua+'\n return base\nend\n')
  sound_paths={p:register(p) for p in converted if p.endswith('.wav')}
  (destination/'sounds.lua').write_text('return function(base)\n local paths={\n'+''.join(' ["'+k+'"]="'+v+'",\n' for k,v in sorted(sound_paths.items()))+' }\n for k,v in pairs(base.fixed_files) do base.fixed_files[k]=paths[v] or v end\n for k,v in pairs(base.menu) do base.menu[k]=paths[v] or v end\n return base\nend\n')
  report={'pack_id':pack_id,'fighters':fighters,'objects':len(records),'backgrounds':len(bgs),'assets':len(converted),'source_catalog_sha256':catalog_sha256,'mode':'isolated, original IDs retained','executable_patches_emulated':False,'gameplay_verified':False,'png_aliases':aliases,'catalog_markers_not_emulated':markers,'custom_catalog_labels':custom_labels,'missing_resources':sorted(missing),'experimental':True}
  if killer:
   report['campaign_available']=not no_campaign
   report['killer_integer_normalization']=killer_repairs
  if id_repair:
   report['mode']='isolated, one conflicting object ID reassigned'
   report['catalog_id_repair']=id_repair
  if normalized_files:
   report['dat_normalization']={
    'edition':normalization[0], 'method':'VC80 x86 sscanf %d',
    'fields_changed':sum(item['fields_changed'] for item in normalized_files),
    'files':sorted(normalized_files,key=lambda item:item['path']),
   }
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
 for virtual,path in assets.items():
  if path.suffix=='.dat':
   for match in pattern.finditer(decode(path.read_bytes())):
    name,w,h,columns,rows=match.groups()
    if name.startswith('./a/'):
     name=virtual.rsplit('/a/',1)[0]+'/'+name[2:]
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
