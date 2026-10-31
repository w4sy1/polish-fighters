"""Identify ASF WAVEFORMAT tags without loading any executable code."""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STREAM=bytes.fromhex('9107dcb7b7a9cf118ee600c00c205365')
AUDIO=bytes.fromhex('409e69f84d5bcf11a8fd00805f5c442b')
def inspect(path):
    raw=path.read_bytes();position=raw.find(STREAM)
    if position<0 or raw[position+24:position+40]!=AUDIO:raise ValueError('ASF audio stream not found')
    size=struct.unpack_from('<Q',raw,position+16)[0]
    if size<96 or position+size>len(raw):raise ValueError('Invalid ASF stream object')
    tag,channels,rate=struct.unpack_from('<HHI',raw,position+78)
    return {'asset':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'codec_tag':hex(tag),
            'codec':{0x161:'WMA v2',0x163:'WMA Lossless'}.get(tag,'unknown'),'channels':channels,'sample_rate':rate}
if __name__=='__main__':
    results=[inspect(p) for p in sorted((ROOT/'content-packs/one-piece/assets').rglob('*.wma'))]
    out=ROOT/'validation/remaining-mechanics-2026-10-30/music-codecs.json'
    out.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
