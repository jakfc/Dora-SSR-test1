local GC = require('src.config.GameConfig')
local GS = require('src.config.GameState')
local gs = GS.GameState.instance

local parts = {}
for _, z in ipairs(GC.GameConfig.FOG_ZONES) do
	parts[#parts + 1] = string.format('%s@%d+w%d=%s', z.id, z.x, z.width,
		tostring(gs:isExplored(z.id)))
end
print('FOG ' .. table.concat(parts, ' '))
print(string.format('FOGN exploredTotal=%d fogged=%d radius=%d',
	#GC.GameConfig.FOG_ZONES - gs.foggedCount, gs.foggedCount, GC.GameConfig.FOG_REVEAL_RADIUS))

local lands = {}
for _, id in ipairs({ 'WEST_PADDY', 'EAST_PADDY', 'WEST_SALT_FLAT', 'EAST_SALT_FLAT' }) do
	lands[#lands + 1] = string.format('%s=lvl%d/ready=%s', id, gs:landLevelOf(id),
		tostring(gs:isLandReady(id)))
end
print('LAND ' .. table.concat(lands, ' '))
print(string.format('RECLAIM cost paddy=%d salt=%d yield paddy=%d salt=%d maxLv=%d',
	GC.GameConfig.RECLAIM.COST.PADDY, GC.GameConfig.RECLAIM.COST.SALT,
	GC.GameConfig.RECLAIM.PADDY_YIELD_PER_LEVEL, GC.GameConfig.RECLAIM.SALT_YIELD_PER_LEVEL,
	GC.GameConfig.RECLAIM.MAX_LEVEL))
print(string.format('SPAWN west=%d east=%d innerGateHp=%d innerGateDefX=%d eastGateDefX=%d',
	GC.GameConfig.SPAWN_WEST_X, GC.GameConfig.SPAWN_EAST_X,
	gs.innerGateHp or -1, gs:getFrontDefenseX(), GC.GameConfig.EAST_GATE_DEFENSE_X))
print(string.format('PACE speed=%.2f day=%d', GC.GameConfig.GAME_SPEED, GC.GameConfig.DAY_DURATION))
