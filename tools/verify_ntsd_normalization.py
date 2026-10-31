"""Recheck materialized NTSD data against preserved originals and actual VC80 output."""
import hashlib,json,subprocess
from pathlib import Path
from import_legacy import decode
from normalize_ntsd_vc80 import normalize
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    pack=ROOT/'content-packs/ntsd';proof=json.loads((pack/'vc80-integer-normalization.json').read_text())
    tokens=list(proof['unique_tokens'])
    result=subprocess.run([str(ROOT/'engine/build/vc80-probe/vc80-scan-probe.exe')],input='\n'.join(tokens)+'\n',text=True,capture_output=True,check=True)
    values={}
    for line in result.stdout.splitlines():
        token,count,value=line.split();assert count=='1';values[token]=int(value)
    assert values==proof['unique_tokens']
    checks=json.loads((pack/'asset-checksums.json').read_text());total=0
    for entry in proof['files']:
        old=(ROOT/'../baseline-remaining-mechanics-2026-10-30/content-packs/ntsd'/entry['asset']).read_bytes()
        new=(pack/entry['asset']).read_bytes()
        assert hashlib.sha256(old).hexdigest()==entry['before_sha256']
        assert hashlib.sha256(new).hexdigest()==entry['after_sha256']==checks[entry['asset']]
        expected,evidence=normalize(decode(old),values)
        assert decode(new)==expected and evidence==entry['fields'] and old[:123]==new[:123]
        total+=len(evidence)
    assert total==proof['field_count']
    out={'verified_files':len(proof['files']),'verified_fields':total,'actual_x86_vc80_reprobe':True,'headers_preserved':True,'asset_hashes_match':True}
    (ROOT/'validation/remaining-mechanics-2026-10-30/ntsd-normalization-verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(out)
