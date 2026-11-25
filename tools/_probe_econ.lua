local GameConfig = require("src.config.GameConfig").GameConfig
local GameState = require("src.config.GameState").GameState
local gs = GameState.instance
local R = GameConfig.RECLAIM
local P = GameConfig.PLAYER
local function n(v) if type(v) == "number" then return v end return -1 end
local out = {}
out[#out+1] = string.format("ECON initial=%d bag=%d unit=%s recruit=%d",
    n(GameConfig.INITIAL_SILVER), n(GameConfig.SILVER_BAG), tostring(GameConfig.SILVER_NAME),
    n(GameConfig.RECRUIT_VILLAGER_COST))
out[#out+1] = string.format("HOUSE build=%d lv2=%d lv3=%d",
    n(GameConfig.HOUSE_BUILD_COST), n(GameConfig.HOUSE_UPGRADE_COST_LV2), n(GameConfig.HOUSE_UPGRADE_COST_LV3))
out[#out+1] = string.format("HALL=%d INNER=%d EAST=%d",
    n(GameConfig.ANCESTRAL_HALL_UPGRADE_BASE_COST), n(GameConfig.INNER_GATE_UPGRADE_COST),
    n(GameConfig.EAST_GATE_UPGRADE_BASE_COST))
out[#out+1] = string.format("RECLAIM cost paddy=%d salt=%d yield paddy=%d salt=%d maxLv=%d",
    R.COST.PADDY, R.COST.SALT, R.PADDY_YIELD_PER_LEVEL, R.SALT_YIELD_PER_LEVEL, R.MAX_LEVEL)
out[#out+1] = string.format("INCOME saltTrip=%d dropCaught=%d scavengeSalt=%d scavengeWood=%d",
    n(GameConfig.SALT_FETCH.tripSilver), n(GameConfig.SALT_FETCH.dropSilverIfCaught),
    n(GameConfig.SCAVENGE_SALT_SILVER), n(GameConfig.SCAVENGE_WOOD_REPAIR))
out[#out+1] = string.format("BRIBE scout=%d samurai=%d boss=%d",
    n(GameConfig.BRIBE_COST.SCOUT), n(GameConfig.BRIBE_COST.SAMURAI), n(GameConfig.BRIBE_COST.BOSS))
local tools = {}
for k, v in pairs(GameConfig.ROLES) do
    if v.toolCost > 0 then tools[#tools+1] = string.format("%s=%d", k, v.toolCost) end
end
table.sort(tools)
out[#out+1] = "TOOLS " .. table.concat(tools, " ")
local towers = {}
for i = 1, #GameConfig.TOWER_SLOTS do
    local t = GameConfig.TOWER_SLOTS[i]
    towers[#towers+1] = string.format("%s=%d", t.id, t.unlockCost)
end
out[#out+1] = "TOWERS " .. table.concat(towers, " ")
out[#out+1] = string.format("TOWERUP arrow=%d cannon=%d",
    n(GameConfig.TOWER_STATS.ARROW.upgradeCost), n(GameConfig.TOWER_STATS.CANNON.upgradeCost))
local en = {}
for k, v in pairs(GameConfig.ENEMIES) do en[#en+1] = string.format("%s=%d", k, v.rewardSilver) end
table.sort(en)
out[#out+1] = "REWARD " .. table.concat(en, " ")
local waves = {}
for i = 1, #GameConfig.NIGHT_WAVES do waves[#waves+1] = tostring(GameConfig.NIGHT_WAVES[i].rewardSilver) end
out[#out+1] = "WAVES " .. table.concat(waves, ",")
out[#out+1] = string.format("LIGHT range=%d dmg=%d cd=%.2f | QILIN dmg=%d cd=%.2f dash=%d",
    P.lightRange, P.lightDamage, P.lightCooldown, P.attackDamage, P.attackCooldown, P.dashDistance)
out[#out+1] = string.format("RUNTIME silver=%d food=%d animScale=%.3f zoom=%.2f",
    n(gs and gs.silver), n(gs and gs.food), n(GameConfig.ANIM_TIME_SCALE), (function() local ok,m = pcall(require,"src.config.Screen") if ok then return n(m.WORLD_ZOOM) end return -1 end)())
print(table.concat(out, "\n"))
