"""Repair the uniquely evidenced unnamed transform entry in the imported Kate pack.
350 is inferred from incoming hit_ja:350 and the existing 351+ sequence, not
claimed as an observed original-engine execution. Original source is retained.
"""
import hashlib
import json
import re
from pathlib import Path
from import_legacy import decode,encode

PIN='eecd725194edf0c872767b6a7275ac1dd5f80991aefc8611b5dcec0096aeaeda'


def repair(text):
    marker=re.compile(r'<frame>\s+transform\b')
    if len(marker.findall(text))!=1 or re.search(r'<frame>\s+350\b',text):
        raise ValueError('Ambiguous or already repaired frame')
    if not re.search(r'hit_ja:\s*350\b',text) or not re.search(r'<frame>\s+351\s+transform\b',text):
        raise ValueError('Missing incoming/continuation evidence')
    return marker.sub('<frame> 350 transform',text,count=1)


if __name__=='__main__':
    path=Path('content-packs/kate/assets/a/000700.dat');raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('Unexpected imported source hash')
    result=encode(repair(decode(raw)),raw);path.write_bytes(result)
    Path('content-packs/kate/data-repairs.json').write_text(json.dumps([{
        'asset':'assets/a/000700.dat','before_sha256':PIN,'after_sha256':hashlib.sha256(result).hexdigest(),
        'change':'Unnamed transform frame assigned 350','evidence':'Incoming hit_ja350 and existing frame351 transform; unique missing entry',
        'inferred':True,'original_runtime_verified':False}],indent=2)+'\n')
