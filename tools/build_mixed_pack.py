"""Build an isolated experimental mixed roster; never alters imported source packages."""
import hashlib
import json
import re
import shutil
from pathlib import Path
from import_legacy import decode,encode

ROOT=Path(__file__).resolve().parents[1]
PACKS=['lf4-turbo','dbz','one-piece','kate','reinforced','ntsd','bleach']
OBJECT=re.compile(r'id:\s*(\d+)\s+type:\s*(\d+)\s+file:\s*(\S+)')

def assets(root):
    return dict(line[6:].split('|',1) for line in (root/'package.manifest').read_text().splitlines() if line.startswith('asset='))

def source(root):
    return re.search(r'base.source_path\s*=\s*"([^"]+)"',(root/'catalog.lua').read_text())[1]

def remap_text(text,mapping,paths,missing):
    def object_id(match):
        old=int(match[2])
        if old==0:return match[0]
        if old not in mapping:missing.add(old)
        # Unknown targets receive their own absent ID; never fall through to another mod.
        return match[1]+str(mapping.get(old,900000+old))
    text=re.sub(r'(\boid:\s*)(\d+)',object_id,text)
    def transform(match):
        state=int(match[2])
        if 3000<=state<4000:
            old=state-3000
            if old not in mapping:missing.add(old)
            return match[1]+str(300000+mapping.get(old,900000+old))
        return match[0]
    text=re.sub(r'(\bstate:\s*)(\d+)',transform,text)
    # Asset names have already been canonicalized by the source importer.
    text=re.sub(r'mods/[a-z0-9-]+/[a-z0-9_./-]+',lambda m:paths.get(m[0],m[0]),text)
    return text

def build(destination=None):
    output=destination or ROOT/'content-packs/mixed-all'
    output.mkdir(parents=True,exist_ok=True)
    generated=output/'assets';generated.mkdir(exist_ok=True)
    own=ROOT/'content-packs/polish-originals'
    own_assets=assets(own)
    own_catalog=(own/own_assets[source(own)]).read_text(encoding='latin1')
    objects=[(int(i),int(k),p) for i,k,p in OBJECT.findall(own_catalog)]
    base_bgs=re.search(r'<background>(.*?)<background_end>',own_catalog,re.S)[1]
    backgrounds=[p for _,p in re.findall(r'id:\s*(\d+)\s+file:\s*(\S+)',base_bgs)]
    manifests=[];metadata={};report=[];all_ids={i for i,_,_ in objects}
    dbz_modules=[]
    for group,pack in enumerate(PACKS,1):
        root=ROOT/'content-packs'/pack;files=assets(root)
        # Background tokens are even shorter than object tokens (29 versus 35 bytes).
        paths={old:f'mods/mixed-all/{group}/{index:05d}'+Path(old).suffix for index,old in enumerate(files)}
        assert all(len(path)<=29 for path in paths.values())
        catalog=(root/files[source(root)]).read_text(encoding='latin1')
        records=[(int(i),int(k),p) for i,k,p in OBJECT.findall(catalog)]
        mapping={}
        for old,_,_ in records:
            if old not in mapping:mapping[old]=1000+len(metadata)+len(mapping)
        assert not all_ids.intersection(mapping.values())
        all_ids.update(mapping.values());missing=set()
        if pack=='dbz':
            scenes=(root/'scene-modes.lua').read_text()
            scenes=re.sub(r'mods/dbz/[a-z0-9_./-]+',lambda m:paths.get(m[0],m[0]),scenes)
            scenes=re.sub(r'(\["oid"\]=)(\d+)',lambda m:m[1]+str(mapping.get(int(m[2]),900000+int(m[2]))),scenes)
            (output/'dbz_scenes.lua').write_text(scenes)
            (output/'dbz_background.lua').write_text((root/'background.lua').read_text().replace('dbz/scene-modes','mixed-all/dbz_scenes'))
            (output/'dbz_runtime.lua').write_text((root/'scene_runtime.lua').read_text())
            (output/'dbz_music.lua').write_text((root/'music.lua').read_text())
            dbz_modules=['module=dbz_scenes|dbz_scenes.lua','module=dbz_runtime|dbz_runtime.lua',
                'extend=base/game/background|dbz_background.lua','extend=base/game/music|dbz_music.lua',
                'extend=base/game/match|dbz_match.lua']
        for old,kind,path in records:
            new=mapping[old];objects.append((new,kind,paths[path]))
            metadata[new]={'pack':pack,'id':old}
        for virtual,relative in files.items():
            src=root/relative
            if not src.is_file():raise FileNotFoundError(src)
            dest_rel=pack+'/'+relative
            dst=generated/dest_rel;dst.parent.mkdir(parents=True,exist_ok=True)
            raw=src.read_bytes()
            if virtual.endswith('.dat'):
                text=decode(raw)
                # Campaign files are retained for provenance; mixed mode currently uses LF2 stages.
                raw=encode(remap_text(text,mapping,paths,missing),raw[:123])
                dst.write_bytes(raw)
            elif virtual.endswith('.txt'):
                dst.write_text(remap_text(raw.decode('latin1'),mapping,paths,missing),encoding='latin1')
            elif not dst.exists() or dst.stat().st_size!=src.stat().st_size or dst.stat().st_mtime_ns!=src.stat().st_mtime_ns:
                shutil.copy2(src,dst)
            manifests.append('asset='+paths[virtual]+'|assets/'+dest_rel)
        bg=re.search(r'<background>(.*?)<background_end>',catalog,re.S)
        if bg:
            backgrounds.extend(paths.get(p,p) for _,p in re.findall(r'id:\s*(\d+)\s+file:\s*(\S+)',bg[1]))
        report.append({'pack':pack,'objects':len(records),'assets':len(files),
                       'unresolved_source_ids':sorted(missing),'mapping':mapping})
    text='<object>\n'+''.join(f'id: {i} type: {kind} file: {path}\n' for i,kind,path in objects)+'<object_end>\n<background>\n'
    text+=''.join(f'id: {n} file: {path}\n' for n,path in enumerate(backgrounds))+'<background_end>\n'
    (generated/'catalog.txt').write_text(text,encoding='latin1')
    manifests.append('asset=mods/mixed-all/catalog.txt|assets/catalog.txt')
    manifest=['id=mixed-all','version=1','api=1','requires=base@1','requires=polish-fighters@1',
      'requires=polish-originals@1','module=metadata|metadata.lua','extend=base/game/catalog|catalog.lua',
      'extend=base/game/frame_rules|frame_rules.lua','extend=base/game/constants|constants.lua']
    (output/'package.manifest').write_text('\n'.join(manifest+dbz_modules+manifests)+'\n')
    lua='return {\n'+''.join(f'[{i}]={{pack="{v["pack"]}",id={v["id"]}}},\n' for i,v in sorted(metadata.items()))+'}\n'
    (output/'metadata.lua').write_text(lua)
    summary={'experimental':True,'objects':len(objects),'maps':len(backgrounds),
      'assets':len(manifests),'unique_ids':len(all_ids),'packs':report,
      'limits':'Generic DAT/opoint and record transforms; EXE/AngelScript behaviors and mixed campaigns are not emulated.'}
    (output/'build-report.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='packs'}))
    return summary

if __name__=='__main__':build()
