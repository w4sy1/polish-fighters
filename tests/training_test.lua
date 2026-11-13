local training=require('base/game/training')
local config={mode=0,training=true,slots={[0]={kind='human',fighter=3,team=1}}}
training.prepare(config)
assert(config.slots[1].kind=='computer' and config.slots[1].fighter==3 and config.slots[1].team==2)
local actor={record={kind=0},human=true,hp=500,mp=200,frame=5,keys={right=true,attack=true}}
local dummy={record={kind=0},hp=0,max_hp=500}
local s={training=true,round_counter=40,items={[0]=actor,[11]=dummy}}
training.reset(s)
assert(dummy.hp==500 and dummy.frame==0 and dummy.vy==0 and s.round_counter==0)
local lines=training.lines(s)
assert(lines[2]:find('right') and lines[2]:find('attack') and lines[3]:find('MP: 200'))
local online={mode=0,training=true,network=true,slots={[0]={kind='human',fighter=3,team=1}}}
training.prepare(online);assert(not online.slots[1],'training replaced a network participant')
print('PASS training: real roster selection, passive respawning dummy, input/frame/MP/clone display and network isolation')
