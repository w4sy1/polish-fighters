-- Generated from package manifests; file presence is not proof of complete mechanics.
return {
 ["polish_fighters"]={assets=50,missing=0,fighters=6},
 ["lf_two"]={assets=1,missing=0,fighters=nil},
 ["lf_four_turbo"]={assets=975,missing=0,fighters=32},
 ["dbz"]={assets=2120,missing=0,fighters=56},
 ["one_piece"]={assets=1179,missing=0,fighters=61},
 ["kate"]={assets=744,missing=0,fighters=29},
 ["reinforced"]={assets=687,missing=0,fighters=28},
 ["ntsd"]={assets=1121,missing=0,fighters=42},
 ["bleach"]={assets=753,missing=0,fighters=34},
 -- 2026-11-23: dragon_ball_super/ntsd_community/mortal_kombat/lf3/oplos promoted from
 -- hub.optional_profiles into hub.profiles (see hub.lua). tools/generate_module_registry.py
 -- needs the real binary assets under content-packs/<id>/ to compute these, which this checkout
 -- does not have (only the 6 small text/manifest files per pack are tracked here) - running it
 -- in this environment would have wrongly marked every asset "missing". assets/missing below are
 -- transcribed from the import descriptions already recorded in mod_catalog.lua for these packs;
 -- fighters is counted from the tracked content-packs/<id>/import-report.json. Re-run
 -- tools/generate_module_registry.py on a checkout with the full assets to confirm/replace these.
 ["dragon_ball_super"]={assets=786,missing=0,fighters=23},
 ["ntsd_community"]={assets=1560,missing=0,fighters=78},
 ["mortal_kombat"]={assets=447,missing=0,fighters=15},
 ["lf3"]={assets=2128,missing=7,fighters=64},
 ["oplos"]={assets=1179,missing=4,fighters=61},
}
