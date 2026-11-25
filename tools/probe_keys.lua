-- 探针：列出已加载的模块名（用来找到 GameState 模块的实际路径）
local keys = {}
for k in pairs(package.loaded) do
	if type(k) == 'string' and (k:find('Game') or k:find('game')) then
		keys[#keys + 1] = k
	end
end
table.sort(keys)
print('KEYS ' .. #keys)
for i = 1, #keys do print(keys[i]) end
