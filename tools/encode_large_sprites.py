"""Losslessly serialize large BMP sprites as RGB PNG for existing loader limits.

No scaling, padding, drawing or pixel substitution. Original BMPs are retained;
only declared resource mappings change. Requires SDL 3.4 PNG support.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from import_legacy import decode, encode


def convert(package, limit=16*1024*1024):
    package=Path(package).resolve();manifest=package/'package.manifest'
    before=manifest.read_text();mapping={};evidence=[]
    # Prepare and verify all new images before modifying references.
    for line in before.splitlines():
        if not line.startswith('asset='):continue
        virtual,relative=line[6:].split('|',1);path=(package/relative).resolve()
        if not path.is_relative_to(package):raise ValueError('Asset escapes package')
        if path.suffix.lower()!='.bmp' or path.stat().st_size<=limit:continue
        target=path.with_suffix('.png')
        if target.exists():raise ValueError('Target already exists: '+str(target))
        with Image.open(path) as source:
            if max(source.size)>8192 or source.width*source.height>16*1024*1024:
                raise ValueError('Image exceeds native dimension/pixel limits')
            # The engine ignores unused BMP alpha bytes and applies black color keys.
            pixels=source.convert('RGB');digest=hashlib.sha256(pixels.tobytes()).hexdigest()
            pixels.save(target,format='PNG',compress_level=9)
            dimensions=list(pixels.size)
        with Image.open(target) as decoded:
            if list(decoded.size)!=dimensions or hashlib.sha256(decoded.convert('RGB').tobytes()).hexdigest()!=digest:
                raise ValueError('Lossless verification failed')
        if target.stat().st_size>limit:raise ValueError('PNG still exceeds loader limit')
        new_virtual=virtual[:-4]+'.png';new_relative=relative[:-4]+'.png'
        mapping[virtual]=new_virtual
        evidence.append({'original':relative,'encoded':new_relative,'dimensions':dimensions,
                         'rgb_sha256':digest,'original_bytes':path.stat().st_size,
                         'encoded_bytes':target.stat().st_size,'original_retained':True})
        before=before.replace('asset='+virtual+'|'+relative,'asset='+new_virtual+'|'+new_relative)
    # LF2 data references use the same encrypted format; headers remain exact.
    for path in sorted((package/'assets').rglob('*.dat')):
        raw=path.read_bytes();text=decode(raw);changed=text
        for source,target in mapping.items():changed=changed.replace(source,target)
        if changed!=text:path.write_bytes(encode(changed,raw))
    manifest.write_text(before)
    (package/'lossless-image-encodings.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return evidence


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('package');a=p.parse_args()
    print(json.dumps(convert(a.package),indent=2))
