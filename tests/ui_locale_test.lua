local saved={}
engine={read_settings=function() return saved end,read_resource=function() return nil end}
local options=require('base/game/options')
assert(options.load().language=='polish','new configuration must start in Polish')
saved={options={language='english'}}
assert(options.load().language=='english','saved language must be preserved')
local pl=require('base/i18n/polish')
assert(pl['Character Selection （選擇角色）']=='Wybór postaci')
assert(pl['按 攻擊 加入!']=='','duplicate Chinese join line must be removed')
for key,value in pairs(require('base/i18n/english')) do
 assert(pl[key]~=nil,'missing bilingual label: '..key)
 if value~='' and value~='OK' and value~='OK!' and value~='E-mail' and value~='Zero' then
  assert(pl[key]~=value,'untranslated bilingual label: '..key)
 end
end
local controls=require('base/ui/controls')
local sets={}
for player=1,4 do sets[player]={device=0,keys={0,0,0,0,0,0,0},buttons={0,1,3}} end
local input=controls.read({sets=sets},'?t')
assert(input.filters.text and input[0]=='','text capability leaked into game actions')
print('PASS: Polish startup, saved language preservation and text-capability isolation')
