"""Create local full game, source-only Studio project, and redistributable core ZIP.
Never includes userdata, credentials, third-party game data in the GitHub artifacts.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'engine/out/PolishFighters-2026-10-30'

def write_zip(path,files,extra=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(path,'w',ZIP_DEFLATED,compresslevel=6) as archive:
        for source,name in sorted(files,key=lambda pair:pair[1]):archive.write(source,name)
        for name,text in (extra or {}).items():archive.writestr(name,text)
    return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    global STAGE
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true')
    parser.add_argument('--stage',type=Path,default=STAGE)
    parser.add_argument('--label',default='2026-10-30')
    args=parser.parse_args();STAGE=args.stage.resolve()
    if not re.fullmatch(r'[A-Za-z0-9-]+',args.label):raise ValueError('Unsafe delivery label')
    label=args.label
    results=[]
    if args.full:
        files=[(p,'PolishFighters-Windows/'+p.relative_to(STAGE).as_posix()) for p in STAGE.rglob('*') if p.is_file() and 'userdata' not in p.relative_to(STAGE).parts]
        results.append(write_zip(ROOT/f'delivery/PolishFighters-Windows-{label}.zip',files))
    elif (ROOT/f'delivery/PolishFighters-Windows-{label}.zip').is_file():
        existing=ROOT/f'delivery/PolishFighters-Windows-{label}.zip'
        results.append({'path':existing.relative_to(ROOT).as_posix(),'bytes':existing.stat().st_size,'sha256':hashlib.sha256(existing.read_bytes()).hexdigest()})
    files=[]
    for p in STAGE.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(STAGE)
        if rel.parts[0] in ['scripts','licenses','server'] or rel.as_posix() in ['tools/account_service.py','tools/room_relay.py'] or (len(rel.parts)==1 and p.suffix in ['.exe','.dll'] and p.name!='LF2_v2.0a.exe') or p.name in ['LICENSE','THIRD-PARTY-NOTICES.md','LITTLE_FIGHTERS_WINDOWS.md','RAPORT-MIXED-ONLINE.md']:
            files.append((p,rel.as_posix()))
    launcher='@echo off\r\ncd /d "%~dp0"\r\n"%~dp0LittleFighters.exe" --config-dir "%~dp0userdata\\common"\r\nif errorlevel 1 pause\r\n'
    results.append(write_zip(ROOT/f'artifacts/PolishFighters-Windows-core-{label}.zip',files,
        {'Graj-Polish-Fighters.cmd':launcher,'CZYTAJ.txt':'Wlasny silnik i biblioteki. Brak cudzych danych LF2/dodatkow. Uruchom Graj-Polish-Fighters.cmd; przy braku danych gra zaoferuje pobranie przypietego LF2. Mozesz tez dodac posiadany LF2_v2.0a.exe obok programu. Pelna lokalna paczka dodatkow jest osobnym ZIP. Nie przenos pojedynczego EXE bez DLL i scripts.\n'}))
    output=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    files=[];seen=set()
    for name in output:
        if not name or name.startswith(('artifacts/','delivery/','preview/')) or name in seen:continue
        p=ROOT/name
        if not p.is_file() or p.is_symlink():continue
        if '/assets/' in name and name.startswith('content-packs/'):raise ValueError('Third-party assets leaked into source selection')
        if p.suffix in ['.jks','.keystore'] and name!='engine/android/debug.keystore':raise ValueError('Private signing material')
        seen.add(name);files.append((p,name))
    for folder in ['sdl-java','assets/scripts','res']:
        for p in (ROOT/'engine/build/android'/folder).rglob('*'):
            if p.is_file():files.append((p,p.relative_to(ROOT).as_posix()))
    results.append(write_zip(ROOT/f'artifacts/PolishFighters-AndroidStudio-{label}.zip',files))
    (ROOT/'artifacts/checksums.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
