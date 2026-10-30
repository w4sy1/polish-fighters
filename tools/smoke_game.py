#!/usr/bin/env python3
"""Runs real headless matches with separately supplied OpenLF2 and LF2 data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TRACE = '@350_230!,@350_230,*2,c,,c,,c,,c,,c,*180,' + ','.join(['c', ''] * 6) + ',u,,u,,c,*300'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--engine', required=True)
    p.add_argument('--installer', required=True)
    args = p.parse_args()
    settings = ROOT / 'engine/scripts/polish-fighters/settings.lua'
    original = settings.read_bytes()
    reports = ROOT / 'validation'
    reports.mkdir(exist_ok=True)
    command = [str(Path(args.engine).resolve()), '--installer', str(Path(args.installer).resolve()),
               '--scripts', str(ROOT / 'engine/scripts'), '--mod', str(settings.parent),
               '--seed', '42', '--input-trace', TRACE]
    results = []
    try:
        # This tool mutates a source settings file temporarily; do not run alongside gameplay.
        for label, source in [('classic', 'return {allowed_ids={},allow_hidden=false}\n'),
                              ('restricted', 'return {allowed_ids={1,2},allow_hidden=false}\n')]:
            settings.write_text(source)
            outputs=[]
            for attempt in range(2):
                r = subprocess.run(command, text=True, capture_output=True, timeout=90)
                output=r.stdout+r.stderr
                (reports / f'{label}-{attempt+1}.log').write_text(output)
                if r.returncode or 'screen=match frame=300' not in output:
                    raise RuntimeError(f'{label}: match failed: {output}')
                outputs.append(output)
            if outputs[0] != outputs[1]:
                raise RuntimeError(f'{label}: repeated seed produced different results')
            if label == 'restricted':
                # Human slot 0 and AI slot 11 for this reproducible trace; remaining items are weapons.
                for slot in (0,11):
                    found=re.search(r'item'+str(slot)+r'\{id=(\d+)',outputs[0])
                    if not found or int(found[1]) not in (1,2):
                        raise RuntimeError('Restricted roster was bypassed')
            results.append({'test': label, 'match_frames':300,'runs':2,'deterministic':True})
        report={'runtime':'upstream prebuilt OpenLF2 v1.1.1, project Lua scripts',
                'installer_sha256':hashlib.sha256(Path(args.installer).read_bytes()).hexdigest(),
                'tests':results,'native_fork_compiled':False,'visual_qa':False,
                'android_device_test':False,'windows_device_test':False}
        (reports/'runtime-results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    finally:
        settings.write_bytes(original)

if __name__ == '__main__': main()
