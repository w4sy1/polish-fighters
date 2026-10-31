"""Create a separate complete local Windows delivery, excluding all user data."""
import hashlib
import json
import shutil
from zipfile import ZipFile,ZIP_DEFLATED
from probe_hub_controls import ROOT, PORTABLE, OUT

def main():
    tested=json.loads((OUT/'summary.json').read_text());preserved=json.loads((OUT/'preservation.json').read_text())
    assert tested['pass'] and preserved['pass']
    assert hashlib.sha256((PORTABLE/'LittleFighters.exe').read_bytes()).hexdigest()==tested['binary_sha256']
    assert (PORTABLE/'LittleFighters.exe').read_bytes()==(PORTABLE/'openlf2.exe').read_bytes()
    profiles=['LF2','lf4-turbo','bleach','kate','reinforced','dbz','ntsd','one-piece','polish-originals']
    for profile in profiles:
        mod='' if profile=='LF2' else f' --mod "%~dp0content-packs/{profile}"'
        command='"%~dp0LittleFighters.exe" --config-dir "%~dp0userdata/common"'+mod
        (PORTABLE/f'Graj-{profile}.cmd').write_bytes(('@echo off\r\ncd /d "%~dp0"\r\n'+command+'\r\nif errorlevel 1 pause\r\n').encode('ascii'))
    launcher='@echo off\r\ncd /d "%~dp0"\r\n"%~dp0LittleFighters.exe" --config-dir "%~dp0userdata/common"\r\nif errorlevel 1 pause\r\n'
    (PORTABLE/'Graj-Little-Fighters.cmd').write_bytes(launcher.encode('ascii'))
    shutil.copy2(PORTABLE/'Graj-polish-originals.cmd',PORTABLE/'Graj-Polish-Fighters.cmd')
    shutil.copy2(ROOT/'LITTLE_FIGHTERS_WINDOWS.md',PORTABLE/'CZYTAJ-LITTLE-FIGHTERS.md')
    shutil.copy2(ROOT/'PROJECT-STATUS.md',PORTABLE/'PROJECT-STATUS.md')
    shutil.copy2(OUT/'REPORT.md',PORTABLE/'RAPORT-HUB-STEROWANIE.md')
    destination=ROOT/'delivery/LittleFighters-hub-controls-2026-10-31.zip'
    files=[]
    for source in PORTABLE.rglob('*'):
        if not source.is_file():continue
        relative=source.relative_to(PORTABLE)
        if 'userdata' in relative.parts or 'recording' in relative.parts:continue
        assert source.suffix.lower() not in ('.jks','.keystore','.env')
        # New art is stored once, under art/. Ignore the old unused local duplicates.
        if relative.parts[:3]==('content-packs','polish-originals','assets') and source.suffix=='.png':continue
        files.append((source,'LittleFighters/'+relative.as_posix()))
    with ZipFile(destination,'w',ZIP_DEFLATED,compresslevel=6) as archive:
        for source,name in sorted(files,key=lambda pair:pair[1]):archive.write(source,name)
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert 'LittleFighters/LittleFighters.exe' in archive.namelist()
    report={'zip':str(destination),'bytes':destination.stat().st_size,'files':len(files),
      'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'crc_pass':True,'userdata_excluded':True}
    (OUT/'delivery.json').write_text(json.dumps(report,indent=2)+'\n')
    destination.with_suffix('.zip.sha256').write_text(report['sha256']+'  '+destination.name+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
