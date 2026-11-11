"""Run actual new Windows engine with isolated inputs and seven forced skill entries."""
import json
from pathlib import Path
import probe_polish_originals as originals
from probe_native_packs import probe
from stage_remonoko import ROOT, STAGE

OUT = ROOT / 'validation/remonoko-2026-11-06'


def main():
    originals.OUT, originals.PORTABLE = OUT, STAGE
    scripted = originals.skills(414, frames=1050)
    events = scripted.get('evidence', {}).get('events', {})
    scripted['pass'] = bool(scripted['pass'] and all(events.get(key, 0) > 0 for key in (
        'spawn_428', 'spawn_429', 'rn_flame', 'rn_teleport', 'rn_mech'))
        and scripted['evidence'].get('seen', {}).get('415'))
    scripted['pass']=scripted['pass'] and scripted['evidence'].get('final_record')==415
    real = probe('polish-originals', 414, OUT / 'native', runs=2,
                 geometry=True, combat=True, binary=STAGE / 'LittleFighters.exe')
    # Exercise the packaged scripts/assets, not only the working-tree version.
    packaged = probe('polish-originals', 414, OUT / 'packaged', runs=1,
                     geometry=True, combat=True, binary=STAGE / 'LittleFighters.exe',
                     scripts=STAGE / 'scripts', content_root=STAGE / 'content-packs')
    report = {'scripted': scripted, 'real_inputs': real, 'packaged_inputs': packaged}
    (OUT / 'native-summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if not scripted['pass']:
        raise AssertionError('Seven skill/transform native probe failed')
    for result in (real, packaged):
        assert result['pass'], result


if __name__ == '__main__':
    main()
