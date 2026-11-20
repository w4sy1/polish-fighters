local commands=require('base/game/team_commands')
local function actor(team,x,human)
 return {record={id=0,kind=0},hp=500,team=team,x_int=x,z_int=300,human=human,keys={},previous_keys={}}
end
local s={items={[0]=actor(1,400,true),[1]=actor(2,400,true),[10]=actor(1,100),[11]=actor(2,200)},mode=1}
assert(commands.input(s,0,'udlrc')=='')
assert(s.items[10].team_command=='come' and not s.items[11].team_command)
assert(s.items[0].team_order_label=='come' and not s.items[10].team_order_label)
s.items[0].team_order_ticks=20
commands.input(s,0,'udlrc')
assert(s.items[0].team_order_ticks==20,'held input renewed the order bubble')
assert(commands.control(s,10) and s.items[10].keys.right)
commands.input(s,0,'');commands.input(s,0,'udlrb')
assert(s.items[0].team_order_label=='stay')
s.items[10].x_int=300
assert(commands.control(s,10) and s.items[10].keys.left,'STAY lost its anchor')
commands.input(s,0,'');commands.input(s,0,'udlrcb')
assert(s.items[0].team_order_label=='defend')
assert(commands.control(s,10) and s.items[10].keys.defend,'DEFEND does not guard position')
commands.input(s,0,'');commands.input(s,0,'udlrf')
assert(s.items[0].team_order_label=='attack')
assert(not commands.control(s,10),'ATTACK did not restore combat AI')
s.items[0].hp=0
commands.issue(s,0,'stay');assert(s.items[10].team_command=='attack','dead owner issued an order')
commands.issue(s,1,'defend')
assert(s.items[1].team_order_label=='defend','a second player needs an independent bubble')
s.items[11].hp=0
s.items[1].team_order_label=nil
commands.issue(s,1,'come')
assert(not s.items[1].team_order_label,'displayed an order without a live recipient')
local recording=require('base/game/recording')
for name,signal in pairs(commands.signals) do
 assert(commands.decode(recording.unpack_keys(recording.pack_keys(signal)))==name,'recording lost command')
end
assert(commands.decode('rc')==nil and commands.decode('udlr')==nil)
print('PASS team commands: filters, follow/stay/attack/defend AI and recording bits')
