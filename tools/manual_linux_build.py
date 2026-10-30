#!/usr/bin/env python3
"""Experimental Linux x86_64 build using prepared source headers and OpenLF2 runtime libraries.
Does not install dependencies or create Windows/Android binaries. See BUILD_LOCAL.md.
"""
import argparse,concurrent.futures,hashlib,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--deps',type=Path,required=True);p.add_argument('--runtime-libs',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--jobs',type=int,default=3);a=p.parse_args()
 if sys.platform!='linux' or platform.machine() not in ('x86_64','AMD64') or sys.byteorder!='little':p.error('This recipe has only been validated on Linux x86_64 little endian')
 engine=ROOT/'engine';deps=a.deps.resolve();lib=a.runtime_libs.resolve();out=a.build_dir.resolve();out.mkdir(parents=True,exist_ok=True);generated=out/'generated';generated.mkdir(exist_ok=True)
 if not (generated/'bzlib.h').is_file():p.error('Provide bzip2 1.0.8 bzlib.h under BUILD_DIR/generated first')
 native_files=sorted(set([*engine.joinpath('src').rglob('*.cpp'),*engine.joinpath('src').rglob('*.mm'),*engine.joinpath('src').rglob('*.hpp'),*engine.joinpath('include').rglob('*.hpp')]))
 identity=''.join(path.relative_to(engine).as_posix()+':'+hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()+'\n' for path in native_files)
 native_signature=hashlib.sha256(identity.encode()).hexdigest()
 generated.joinpath('openlf2_build_info.hpp').write_text('#pragma once\n#define OPENLF2_BUILD_LABEL "Polish Fighters 0.6 local build"\n#define OPENLF2_ENGINE_SIGNATURE "'+native_signature+'"\n')
 avconfig=deps/'FFmpeg/libavutil/avconfig.h'
 if not avconfig.is_file():avconfig.write_text('#ifndef AVUTIL_AVCONFIG_H\n#define AVUTIL_AVCONFIG_H\n#define AV_HAVE_BIGENDIAN 0\n#define AV_HAVE_FAST_UNALIGNED 1\n#endif\n')
 sources=[]
 for folder in ['core','resources','engine']:sources+=list((engine/'src'/folder).glob('*.cpp'))
 for name in ['compression/decompressor.cpp','crypto/sha256.cpp','luajit/runtime.cpp','ffmpeg/music_decoder.cpp','network/transport.cpp','curl/downloader.cpp']:sources.append(engine/'src/adapters'/name)
 for name in ['entry.cpp','platform.cpp','setup_screen.cpp','frame_upscaler.cpp','gl_upscaler.cpp','gpu_upscaler.cpp','sprite_effects.cpp','text_renderer.cpp','haptics_stub.cpp']:sources.append(engine/'src/adapters/sdl'/name)
 sources.append(engine/'src/app/application.cpp')
 flags=['-std=c++23','-O1','-g0','-Wall','-Wextra','-Wpedantic','-Wconversion','-Wshadow','-Werror','-pthread','-DOPENLF2_DEFAULT_JIT=1','-DOPENLF2_SIMULATION_THREADS','-I',str(engine/'include'),'-I',str(generated)]
 for path in [deps/'LuaJIT/src',deps/'SDL/include',deps/'SDL_ttf/include',deps/'FFmpeg']:flags+=['-isystem',str(path)]
 headers=hashlib.sha256()
 for path in sorted((engine/'include').rglob('*.hpp')):headers.update(path.relative_to(engine).as_posix().encode());headers.update(path.read_bytes())
 headers.update(generated.joinpath('openlf2_build_info.hpp').read_bytes());headers_hash=headers.hexdigest()
 flag_hash=hashlib.sha256(json.dumps(flags).encode()).hexdigest()
 manifest_path=out/'build-manifest.json';previous=json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
 def compile_one(source):
  relative=source.relative_to(engine/'src').as_posix();obj=out/(relative.replace('/','_')+'.o');fingerprint=digest(source)+headers_hash+flag_hash
  if previous.get('objects',{}).get(relative)==fingerprint and obj.is_file():print(relative,'CACHED',flush=True);return relative,obj,fingerprint,0
  result=subprocess.run(['g++',*flags,'-c',str(source),'-o',str(obj)],capture_output=True,text=True)
  (out/(obj.name+'.log')).write_text(result.stdout+result.stderr);print(relative,'OK' if result.returncode==0 else 'FAIL',flush=True)
  if result.returncode:print(result.stderr[:3000],flush=True)
  return relative,obj,fingerprint,result.returncode
 with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(a.jobs,6))) as pool:results=list(pool.map(compile_one,sources))
 if any(code for _,_,_,code in results):return 1
 libs=[str(deps/'LuaJIT/src/libluajit.a')]+[str(lib/name) for name in ['libSDL3.so.0','libSDL3_ttf.so.0','libavformat.so.61','libavcodec.so.61','libavutil.so.59','libswresample.so.5']]
 binary=out/'polish-fighters';command=['g++','-pthread','-o',str(binary),*[str(obj) for _,obj,_,_ in results],*libs,'-lcrypto','-lcurl','-lz','-l:libbz2.so.1.0','-ldl','-lm','-Wl,-rpath,'+str(lib)]
 linked=subprocess.run(command,capture_output=True,text=True);(out/'link.log').write_text(linked.stdout+linked.stderr)
 if linked.returncode:print(linked.stderr);return linked.returncode
 revisions={}
 for name in ['SDL','SDL_ttf','LuaJIT','FFmpeg']:
  revision=subprocess.run(['git','rev-parse','HEAD'],cwd=deps/name,text=True,capture_output=True);revisions[name]=revision.stdout.strip() if revision.returncode==0 else 'unknown'
 manifest={'platform':platform.platform(),'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'objects':{relative:fingerprint for relative,_,fingerprint,_ in results},'headers_sha256':headers_hash,'flags':flags,'dependencies':revisions,'native_signature':native_signature,'binary_sha256':digest(binary),'binary_size':binary.stat().st_size,'type':'complete local Linux engine; prepared shared dependencies required'}
 manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');print('BUILT',binary,manifest['binary_sha256']);return 0
if __name__=='__main__':raise SystemExit(main())
