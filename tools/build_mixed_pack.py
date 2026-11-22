"""Build an isolated experimental mixed roster; never alters imported source packages."""
import argparse
import tempfile
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
    match=re.search(r'base.source_path\s*=\s*"([^"]+)"',(root/'catalog.lua').read_text())
    if not match:
        raise ValueError(f'{root.name}: catalog.lua does not declare base.source_path')
    return match[1]

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

def build(destination=None, *, packs=PACKS, packs_root=ROOT/'content-packs', generated_profile=False):
    output=destination or ROOT/'content-packs/mixed-all'
    # Reuse the loader's published mixed namespace, asset budget and DBZ frame limit.
    # A generated package is passed as an alternative root and is never loaded alongside mixed-all.
    package_id='mixed-all'
    output.mkdir(parents=True,exist_ok=True)
    generated=output/'assets';generated.mkdir(exist_ok=True)
    own=packs_root/'polish-originals'
    own_assets=assets(own)
    own_relative=own_assets[source(own)]
    own_catalog_path=local_file(own,own_relative) if generated_profile else own/own_relative
    own_catalog=own_catalog_path.read_text(encoding='latin1')
    objects=[(int(i),int(k),p) for i,k,p in OBJECT.findall(own_catalog)]
    base_bgs=re.search(r'<background>(.*?)<background_end>',own_catalog,re.S)[1]
    backgrounds=[p for _,p in re.findall(r'id:\s*(\d+)\s+file:\s*(\S+)',base_bgs)]
    manifests=[];metadata={};report=[];all_ids={i for i,_,_ in objects}
    dbz_modules=[]
    for group,pack in enumerate(PACKS,1):
        if pack not in packs:
            continue
        root=packs_root/pack;files=assets(root)
        # Background tokens are even shorter than object tokens (29 versus 35 bytes).
        paths={old:f'mods/{package_id}/{group}/{index:05d}'+Path(old).suffix for index,old in enumerate(files)}
        assert all(len(path)<=29 for path in paths.values())
        catalog_relative=files[source(root)]
        catalog_path=local_file(root,catalog_relative) if generated_profile else root/catalog_relative
        catalog=catalog_path.read_text(encoding='latin1')
        records=[(int(i),int(k),p) for i,k,p in OBJECT.findall(catalog)]
        mapping={}
        for old,_,_ in records:
            if generated_profile:
                if old in mapping:
                    raise ValueError(f'{pack}: duplicate object ID {old}')
                if len(mapping) >= 1000:
                    raise ValueError(f'{pack}: exhausted 1000 reserved object slots')
                mapping[old]=group*1000+len(mapping)
            elif old not in mapping:
                mapping[old]=1000+len(metadata)+len(mapping)
        if all_ids.intersection(mapping.values()):
            raise ValueError(f'{pack}: remapped ID conflicts with the base roster')
        all_ids.update(mapping.values());missing=set()
        if pack=='dbz':
            scenes=(root/'scene-modes.lua').read_text()
            scenes=re.sub(r'mods/dbz/[a-z0-9_./-]+',lambda m:paths.get(m[0],m[0]),scenes)
            scenes=re.sub(r'(\["oid"\]=)(\d+)',lambda m:m[1]+str(mapping.get(int(m[2]),900000+int(m[2]))),scenes)
            (output/'dbz_scenes.lua').write_text(scenes)
            (output/'dbz_background.lua').write_text((root/'background.lua').read_text().replace('dbz/scene-modes',f'{package_id}/dbz_scenes'))
            (output/'dbz_runtime.lua').write_text((root/'scene_runtime.lua').read_text())
            (output/'dbz_music.lua').write_text((root/'music.lua').read_text())
            dbz_modules=['module=dbz_scenes|dbz_scenes.lua','module=dbz_runtime|dbz_runtime.lua',
                'extend=base/game/background|dbz_background.lua','extend=base/game/music|dbz_music.lua',
                'extend=base/game/match|dbz_match.lua']
        for old,kind,path in records:
            new=mapping[old];objects.append((new,kind,paths[path]))
            metadata[new]={'pack':pack,'id':old}
        for virtual,relative in files.items():
            src=local_file(root,relative) if generated_profile else root/relative
            if not src.is_file():raise FileNotFoundError(src)
            dest_rel=paths[virtual].removeprefix(f'mods/{package_id}/') if generated_profile else pack+'/'+relative
            dst=generated/dest_rel;dst.parent.mkdir(parents=True,exist_ok=True)
            raw=src.read_bytes()
            if virtual.endswith('.dat'):
                text=decode(raw)
                # Campaign files are retained for provenance; mixed mode currently uses LF2 stages.
                raw=encode(remap_text(text,mapping,paths,missing),raw[:123])
                dst.write_bytes(raw)
            elif virtual.endswith('.txt'):
                rewritten=remap_text(raw.decode('latin1'),mapping,paths,missing)
                if generated_profile:
                    dst.write_bytes(rewritten.encode('latin1'))
                else:
                    dst.write_text(rewritten,encoding='latin1')
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
    if generated_profile:
        (generated/'catalog.txt').write_bytes(text.encode('latin1'))
        templates=ROOT/'content-packs/mixed-all'
        for filename in ('catalog.lua','frame_rules.lua','constants.lua','dbz_match.lua'):
            if filename=='dbz_match.lua' and not dbz_modules:
                continue
            script=(templates/filename).read_text(encoding='utf-8')
            if filename=='catalog.lua':
                script,replacements=re.subn(r' local selected=.*? assert\(not problem,problem\)\n',
                              ' local selected,hide_duplicates={},false\n',script,flags=re.S)
                if replacements!=1:
                    raise ValueError('Mixed catalog template changed its pack preferences block')
                selection='-'.join(pack for pack in PACKS if pack in packs)
                script=script.replace("base.profile_id='mixed-all'",f"base.profile_id='mod-mix-{selection}'")
            (output/filename).write_bytes(script.encode('utf-8'))
    else:
        (generated/'catalog.txt').write_text(text,encoding='latin1')
    manifests.append(f'asset=mods/{package_id}/catalog.txt|assets/catalog.txt')
    manifest=[f'id={package_id}','version=1','api=1','requires=base@1','requires=polish-fighters@1',
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

def local_file(root, relative):
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'{root.name}: asset path outside the package: {relative}')
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def build_selection(packs, packs_root, destination):
    unsupported=set(packs)-set(PACKS)
    if unsupported:
        raise ValueError('No mixed-mode adapter for: '+', '.join(sorted(unsupported)))
    if not packs or len(set(packs))!=len(packs):
        raise ValueError('Select at least one package and list each only once')
    if destination.exists() or destination.is_symlink():
        raise ValueError(f'Output already exists: {destination}')
    for pack in ('polish-originals', *packs):
        if not (packs_root/pack/'package.manifest').is_file():
            raise FileNotFoundError(f'{pack}: missing installed package in {packs_root}')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.mix-',dir=destination.parent) as temporary:
        output=Path(temporary)/'package'
        summary=build(output,packs=packs,packs_root=packs_root,generated_profile=True)
        output.rename(destination)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packs',nargs='*',help='IDs of installed packages to mix')
    parser.add_argument('--content-packs',type=Path,default=ROOT/'content-packs')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        if args.packs:
            if args.output is None:
                parser.error('--output is required for a selected mix')
            build_selection(args.packs,args.content_packs,args.output)
        elif args.output or args.content_packs!=ROOT/'content-packs':
            parser.error('list the packages to mix')
        else:
            build()
    except (OSError,ValueError,KeyError) as error:
        parser.exit(1,f'Cannot build mixed package: {error}\n')
