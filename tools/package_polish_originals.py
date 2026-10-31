"""Package the tested additive Windows roster; preserve all older deliveries."""
import hashlib
import json
import shutil
from zipfile import ZipFile, ZIP_DEFLATED
from probe_polish_originals import ROOT, PORTABLE, PACK, OUT

def main():
    summary=json.loads((OUT/'native-summary.json').read_text())
    preserved=json.loads((OUT/'preservation-after.json').read_text())
    assert summary['pass'] and preserved['pass']
    assert hashlib.sha256((PORTABLE/'openlf2.exe').read_bytes()).hexdigest()==summary['binary_sha256']
    shutil.copytree(PACK,PORTABLE/'content-packs/polish-originals',dirs_exist_ok=True)
    for title,mod,profile in [('Polish-Fighters',' --mod "%~dp0content-packs/polish-originals"','polish-originals'),
                              ('LF2-Oryginal','','LF2')]:
        launcher=('@echo off\r\ncd /d "%~dp0"\r\n'
          '"%~dp0openlf2.exe" --installer "%~dp0LF2_v2.0a.exe" --scripts "%~dp0scripts" '
          '--mod "%~dp0scripts/polish-fighters"'+mod+' --config-dir "%~dp0userdata/'+profile+'"\r\n'
          'if errorlevel 1 pause\r\n')
        (PORTABLE/f'Graj-{title}.cmd').write_bytes(launcher.encode('ascii'))
    shutil.copy2(PACK/'README_PL.md',PORTABLE/'CZYTAJ-POSTACIE.md')
    shutil.copy2(OUT/'REPORT.md',PORTABLE/'RAPORT-POSTACIE.md')
    shutil.copy2(ROOT/'PROJECT-STATUS.md',PORTABLE/'PROJECT-STATUS.md')
    destination=ROOT/'delivery/PolishFighters-four-characters-2026-10-31.zip'
    destination.parent.mkdir(exist_ok=True)
    files=[]
    for source in PORTABLE.rglob('*'):
        if not source.is_file(): continue
        relative=source.relative_to(PORTABLE)
        assert 'userdata' not in relative.parts
        # Old duplicate atlas copies are deliberately excluded; the manifest uses art/.
        if relative.parts[:3]==('content-packs','polish-originals','assets') and source.suffix=='.png':continue
        assert source.suffix.lower() not in ('.jks','.keystore','.env')
        files.append((source,'PolishFighters/'+relative.as_posix()))
    with ZipFile(destination,'w',ZIP_DEFLATED,compresslevel=6) as archive:
        for source,name in sorted(files,key=lambda pair:pair[1]): archive.write(source,name)
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        names=set(archive.namelist())
        for launcher in ['Graj-Polish-Fighters.cmd','Graj-LF2-Oryginal.cmd']:
            assert 'PolishFighters/'+launcher in names
        for line in (PACK/'package.manifest').read_text().splitlines():
            if line.startswith('asset='):
                _,relative=line[6:].split('|',1)
                assert 'PolishFighters/content-packs/polish-originals/'+relative in names
    report={'path':str(destination),'bytes':destination.stat().st_size,'files':len(files),
      'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'crc_pass':True,'manifest_assets_present':True}
    (OUT/'delivery.json').write_text(json.dumps(report,indent=2)+'\n')
    (destination.parent/(destination.name+'.sha256')).write_text(report['sha256']+'  '+destination.name+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
