local commands=require('base/game/team_commands')
local function actor(team,x,human)
 return {record={id=0,kind=0},hp=500,team=team,x_int=x,z_int=300,human=human,keys={},previous_keys={}}
end
local s={items={[0]=actor(1,400,true),[1]=actor(2,400,true),[10]=actor(1,100),[11]=actor(2,200)},mode=1}
assert(commands.input(s,0,'udlrc')=='')
assert(s.items[10].team_command=='come' and not s.items[11].team_command)
assert(commands.control(s,10) and s.items[10].keys.right)
commands.input(s,0,'');commands.input(s,0,'udlrb')
s.items[10].x_int=300
assert(commands.control(s,10) and s.items[10].keys.left,'STAY lost its anchor')
commands.input(s,0,'');commands.input(s,0,'udlrcb')
assert(commands.control(s,10) and s.items[10].keys.defend,'DEFEND does not guard position')
commands.input(s,0,'');commands.input(s,0,'udlrf')
assert(not commands.control(s,10),'ATTACK did not restore combat AI')
s.items[0].hp=0
commands.issue(s,0,'stay');assert(s.items[10].team_command=='attack','dead owner issued an order')
local recording=require('base/game/recording')
for name,signal in pairs(commands.signals) do
 assert(commands.decode(recording.unpack_keys(recording.pack_keys(signal)))==name,'recording lost command')
end
assert(commands.decode('rc')==nil and commands.decode('udlr')==nil)
engine={read_settings=function() return {} end}
local options=require('base/game/options')
local pad=require('base/ui/touch_gamepad')
local p=pad.create(options.default_gamepad(),false,'modern')
pad.set_available(p,{})
local function touch(t) return pad.update(p,{touch_active=true,touches=t},'match') end
touch({{id=1,x=p.commands.x,y=p.commands.y}});assert(p.command_open)
touch({})
local choice=p.command_choices[2]
local _,_,_,signal=touch({{id=2,x=choice.x,y=choice.y}})
assert(signal=='stay' and not p.command_open and p.confirmation_ticks>0)
assert(not p.held.c and not p.held.b and not p.finger,'bubble selection leaked attack/jump/movement')
local _,_,_,repeated=touch({{id=2,x=choice.x,y=choice.y}})
assert(not repeated,'held bubble generated duplicate command')
pad.update(p,{touch_active=false})
touch({{id=2,x=p.commands.x,y=p.commands.y}})
assert(p.command_open,'finger ID reused after hiding was ignored')
print('PASS team commands: owner/team filters, follow/stay/attack/defend AI, existing recording bits, bubble selection and confirmation')
