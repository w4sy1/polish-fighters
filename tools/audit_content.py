"""Read-only content inventory. Does not run, build or modify game assets."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from import_legacy import decode


def audit(package):
    package = Path(package).resolve(strict=True)
    assets = {}
    for line in (package / 'package.manifest').read_text().splitlines():
        if line.startswith('asset='):
            virtual, relative = line[6:].split('|', 1)
            path = (package / relative).resolve()
            if not path.is_relative_to(package):
                raise ValueError('Asset escapes package: ' + relative)
            if virtual in assets:
                raise ValueError('Duplicate asset: ' + virtual)
            assets[virtual] = path
    report = {'package': package.name, 'scope': 'Static data only; gameplay not verified',
              'assets': len(assets), 'missing_assets': [], 'objects': [],
              'arenas': [], 'campaigns': [], 'integer_overflows': []}
    texts = {}
    for virtual, path in assets.items():
        if not path.is_file():
            report['missing_assets'].append(virtual)
            continue
        if path.suffix == '.dat':
            text = decode(path.read_bytes())
            texts[virtual] = text
            # Numeric field values only: filenames and frame labels are not integers.
            for number in re.finditer(r'\b([a-zA-Z_]+):\s*(-?\d+)(?![\w.])', text):
                if not -2147483648 <= int(number[2]) <= 2147483647:
                    report['integer_overflows'].append({'asset': virtual,
                        'line': text.count('\n', 0, number.start()) + 1,
                        'field': number[1], 'value': number[2]})
    for virtual, path in assets.items():
        if path.suffix != '.txt' or not path.is_file():
            continue
        catalog = path.read_text(encoding='latin1')
        for entry in re.finditer(r'id:\s*(\d+)\s+type:\s*(\d+)\s+file:\s*(\S+)', catalog):
            id_, kind, source = entry.groups()
            text = texts.get(source, '')
            frames = [int(x) for x in re.findall(r'<frame>\s+(\d+)', text)]
            name = re.search(r'\bname:\s*(\S+)', text)
            frame_records=[]
            for frame in re.finditer(r'<frame>\s+(\d+)\s+(\S+)(.*?)<frame_end>', text, re.S):
                # Only the frame header supplies movement/combination transitions;
                # nested point blocks use their own action fields.
                header=re.split(r'\b(?:bpoint|wpoint|cpoint|opoint|itr|bdy):',frame[3],maxsplit=1)[0]
                fields={key:int(value) for key,value in re.findall(r'\b(state|wait|next|hit_[A-Za-z]+):\s*(-?\d+)',header)}
                spawns=[]
                for point in re.finditer(r'\bopoint:(.*?)opoint_end:',frame[3],re.S):
                    spawns.append({key:int(value) for key,value in re.findall(r'\b(kind|oid|action|facing):\s*(-?\d+)',point[1])})
                frame_records.append({'id':int(frame[1]),'name':frame[2],**fields,'spawns':spawns})
            report['objects'].append({'id': int(id_), 'type': int(kind),
                'name': name[1] if name else None, 'asset': source,
                'frames': len(frames), 'duplicate_frames': sorted({x for x in frames if frames.count(x) > 1}),
                'states': sorted({f['state'] for f in frame_records if 'state' in f}),
                'moves': [f for f in frame_records if f['spawns'] or any(k.startswith('hit_') and v for k,v in f.items())],
                'frame_graph':frame_records if int(kind)==0 else [],
                'missing': source not in texts})
        for entry in re.finditer(r'id:\s*(\d+)\s+file:\s*(\S+)', catalog):
            text = texts.get(entry[2], '')
            name = re.search(r'\bname:\s*(\S+)', text)
            report['arenas'].append({'id': int(entry[1]), 'asset': entry[2],
                'name': name[1] if name else None, 'missing': entry[2] not in texts})
    for virtual, text in texts.items():
        stages = re.findall(r'<stage>\s*id:\s*(\d+)', text)
        if stages:
            report['campaigns'].append({'asset': virtual, 'stages': [int(x) for x in stages],
                'phases': len(re.findall(r'<phase>', text)),
                'sha256': hashlib.sha256(assets[virtual].read_bytes()).hexdigest()})
    report['fighters'] = sum(x['type'] == 0 for x in report['objects'])
    ids={x['id'] for x in report['objects']}
    report['unknown_spawn_ids']=[{'object':obj['id'],'frame':frame['id'],'oid':point['oid']}
        for obj in report['objects'] for frame in obj['moves'] for point in frame['spawns']
        if 'oid' in point and point['oid'] not in ids]
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('package', 'assets', 'fighters')}))
    print('Integer overflows:', len(result['integer_overflows']))
