"""Mixed eight-source native match, including Remonoko, rendered and repeated."""
import json
import re
import probe_mixed_pack as mixed
from stage_remonoko import ROOT, STAGE

OUT = ROOT / 'validation/remonoko-2026-11-06/mixed'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mixed.OUT, mixed.BINARY = OUT, STAGE / 'LittleFighters.exe'
    fixture = OUT / 'fixture'
    fixture.mkdir(exist_ok=True)
    (fixture / 'package.manifest').write_text('id=remonoko-mixed-probe\nversion=1\napi=1\nrequires=base@1\nrequires=polish-fighters@1\nrequires=mixed-all@1\nextend=base/ui/flow|flow.lua\n')
    (fixture / 'flow.lua').write_text('''return function(base)
 local update,describe=base.update,base.describe
 local packs={'polish-originals','lf4-turbo','dbz','one-piece','kate','reinforced','ntsd','bleach'}
 function base.update(s,input,context)
  if not s.remonoko_probe then
   s.remonoko_probe=true
   local catalog=require('base/game/catalog');local fighters=catalog.load();local slots={}
   for _,f in ipairs(fighters) do if f.id==415 then assert(not catalog.selectable(f),'mech selectable') end end
   for slot,pack in ipairs(packs) do
    local selected
    for row,fighter in ipairs(fighters) do
     if (pack=='polish-originals' and fighter.id==414) or
       (fighter.pack==pack and catalog.selectable(fighter) and not fighter.name:lower():find('template',1,true)) then
      selected=row;break
     end
    end
    assert(selected,'no fighter for '..pack)
    slots[slot-1]={kind='human',fighter=selected,team=slot%2+1}
   end
   s.match=require('base/ui/match_screen').create({mode=0,difficulty=0,background=0,
     fighters=fighters,backgrounds=catalog.backgrounds(),slots=slots})
   s.active='match';s.wait_release=nil
   for slot=0,7 do local v=s.match.match.items[slot];v.x=70+slot*90;v.x_int=v.x;v.z=400;v.z_int=400 end
  end
  return update(s,input,context)
 end
 function base.describe(s)
  return describe(s)..' remonoko_mixed_digest='..require('polish-fighters/sync_state').digest(s)
 end
 return base
end
''')
    trace = 'c/c/c/c/c/c/c/c*15,*30,r/l/r/l/r/l/r/l*40,c/c/c/c/c/c/c/c*25,*190'
    logs = [mixed.run('fight-' + str(n), trace, fixture, capture=True) for n in range(2)]
    digests = [re.search(r'remonoko_mixed_digest=([a-f0-9]{64})', log)[1] for log in logs]
    assert digests[0] == digests[1], digests
    report = {'pass': True, 'eight_sources': True, 'frames': 300, 'mech_hidden': True,
              'deterministic_digest': digests[0], 'rendered': True}
    (OUT / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
