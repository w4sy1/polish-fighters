local list={[0]={phases={[0]={bound=794,when_clear_goto_phase=-1},[1]={bound=1600,when_clear_goto_phase=-1}}},[1]={phases={}}}
engine={read_stage_data=function() return {stages=list} end}
local advance=require('base/game/campaign_advance')
local run={id=0,phase=0,phase_done=1,result=0,shutter=0,last_phase=0,runtime={[0]={{count=2,total=2}}}}
local s={mode=1,stage_run=run,items={}}
assert(advance.ready(s))
s.items[0]={record={kind=0},hp=500,team=1,x_int=600,z_int=300}
s.items[10]={record={kind=0},hp=500,team=1,x_int=100,z_int=300,keys={},previous_keys={}}
assert(advance.follow(s,10) and s.items[10].keys.right,'ally did not follow through cleared section')
s.items[10].team_command='stay';assert(not advance.follow(s,10),'auto follow overrode STAY')
s.items[0],s.items[10]=nil,nil
local driver={};assert(advance.input(driver,s,'',true)=='r')
assert(advance.input(driver,s,'l',true)=='l')
assert(advance.input(driver,s,'',true)=='','manual takeover was forgotten on release')
run.phase=1;run.last_phase=1;assert(advance.input(driver,s,'',true)=='r')
assert(advance.input({},s,'',false)=='')
s.items[20]={record={kind=0},team=5,hp=1}
assert(not advance.ready(s),'living enemy did not stop auto movement')
s.items[20]=nil;run.runtime[1]={{count=1,total=2}}
assert(not advance.ready(s),'scheduled spawn was skipped')
run.runtime[1]=nil;list[1]=nil
assert(not advance.ready(s),'missing exit was invented')
list[1]={phases={}}
for _,mode in ipairs({0,2,3,4}) do s.mode=mode;assert(not advance.ready(s),'auto movement leaked to another mode') end
print('PASS campaign advance: clear fight, future spawns, real exits, cancellation, option and versus/arena isolation')
