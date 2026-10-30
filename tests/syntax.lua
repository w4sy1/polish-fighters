for i = 1, #arg do assert(loadfile(arg[i])) end
print('PASS: Lua syntax (' .. #arg .. ' files)')
