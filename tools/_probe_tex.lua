local paths = {
	'assets/buildings/b01_shrine.png',
	'assets/buildings/b01_shrine@2x.png',
	'assets/sprites/villagers/villager_militia_01.png',
	'assets/sprites/villagers/villager_militia_01@2x.png',
	'assets/bg/c01_ground_city.png',
	'assets/bg/d01_sky_day.png',
}
for i = 1, #paths do
	local p = paths[i]
	local ok, tex = pcall(function() return Texture2D(p) end)
	if ok and tex then
		print(string.format('TEX %s -> %dx%d', p, tex.width, tex.height))
	else
		print('TEX ' .. p .. ' -> MISSING')
	end
end
