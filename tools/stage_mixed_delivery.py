"""Stage a new local full installation without overwriting earlier deliveries or userdata."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'engine/out/LittleFighters-mixed-online-2026-10-31'
if __name__=='__main__':
 if not STAGE.exists():
  shutil.copytree(ROOT/'engine/out/LittleFighters-pack-ai-2026-10-31',STAGE,
   ignore=shutil.ignore_patterns('userdata','recording','recordings'))
 for name in ['LittleFighters.exe','openlf2.exe']:
  shutil.copy2(ROOT/'engine/build/windows/x64/native/Release/openlf2.exe',STAGE/name)
 shutil.copytree(ROOT/'engine/scripts',STAGE/'scripts',dirs_exist_ok=True)
 # Imported assets are immutable within this dated delivery. Resync scripts without
 # copying the multi-GB asset tree again; a new generated asset set needs a new stage.
 target=STAGE/'content-packs/mixed-all'
 if not (target/'assets/catalog.txt').exists():
  shutil.copytree(ROOT/'content-packs/mixed-all',target,dirs_exist_ok=True)
 else:
  for path in (ROOT/'content-packs/mixed-all').iterdir():
   if path.is_file():shutil.copy2(path,target/path.name)
 for path in (ROOT/'content-packs/dbz').glob('*.lua'):
  shutil.copy2(path,STAGE/'content-packs/dbz'/path.name)
 shutil.copytree(ROOT/'server',STAGE/'server',dirs_exist_ok=True)
 (STAGE/'tools').mkdir(exist_ok=True)
 for name in ['account_service.py','room_relay.py']:
  shutil.copy2(ROOT/'tools'/name,STAGE/'tools'/name)
 shutil.copy2(ROOT/'LITTLE_FIGHTERS_WINDOWS.md',STAGE/'LITTLE_FIGHTERS_WINDOWS.md')
 shutil.copy2(ROOT/'validation/mixed-2026-10-31/REPORT.md',STAGE/'RAPORT-MIXED-ONLINE.md')
 command='@echo off\r\ncd /d "%~dp0"\r\n"%~dp0LittleFighters.exe" --config-dir "%~dp0userdata/common" --mod "%~dp0content-packs/polish-originals" --mod "%~dp0content-packs/mixed-all"\r\nif errorlevel 1 pause\r\n'
 (STAGE/'Graj-Wszystkie-Mody.cmd').write_bytes(command.encode('ascii'))
 print(STAGE)
