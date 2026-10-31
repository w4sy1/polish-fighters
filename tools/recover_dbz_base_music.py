"""Explicit base-LF2 inheritance for DBZ's missing standard bgm/stage4.wma.
This is a compatibility fallback, not proof of the author's intended soundtrack.
"""
import hashlib,json
from pathlib import Path
from read_pinned_lf2 import read_resource,PIN
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    pack=ROOT/'content-packs/dbz';relative='assets/inherited-base/stage4.wma'
    target=pack/relative;virtual='mods/dbz/a/000052.wma'
    source=ROOT/'../downloads/LF2_v2.0a.exe'
    audio=read_resource(source,'bgm/stage4.wma')
    digest=hashlib.sha256(audio).hexdigest()
    if target.exists():assert target.read_bytes()==audio
    else:target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(audio)
    manifest=pack/'package.manifest';text=manifest.read_text();binding='asset='+virtual+'|'+relative
    matches=[line for line in text.splitlines() if line.startswith('asset='+virtual+'|')]
    assert not matches or matches==[binding]
    if not matches:manifest.write_text(text.rstrip()+'\n'+binding+'\n')
    proof={'missing_mod_resource':'bgm/stage4.wma','virtual_resource':virtual,'asset':relative,
           'source':'Pinned original LF2 v2.0a archive; read as data only','source_sha256':PIN,'source_resource':'bgm/stage4.wma',
           'asset_sha256':digest,'scope':'Explicit base-game compatibility fallback; DBZ-specific intended recording not established',
           'original_dbz_audio_recovered':False}
    (pack/'inherited-base-music.json').write_text(json.dumps(proof,indent=2)+'\n')
    hashes=pack/'asset-checksums.json';checks=json.loads(hashes.read_text());checks[relative]=digest
    hashes.write_text(json.dumps(checks,indent=2)+'\n')
    print('Installed explicit LF2 base fallback:',len(audio),'bytes;',digest)
