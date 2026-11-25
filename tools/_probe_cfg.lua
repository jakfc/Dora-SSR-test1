-- 配置探针：地图改版的关键常量是否都就位（只读，不改游戏状态）
local GC = require('src.config.GameConfig')
local C = GC.GameConfig or GC

local function n(v) if v == nil then return 'nil' end return tostring(v) end

print(string.format('MAP width=%s groundY=%s cam=[%s,%s] safe=%s',
  n(C.MAP_WIDTH), n(C.GROUND_Y), n(C.CAMERA_MIN_X), n(C.CAMERA_MAX_X), n(C.SAFE_LINE_X)))
print(string.format('SPAWN west=%s east=%s zone=[%s,%s]',
  n(C.SPAWN_WEST_X), n(C.SPAWN_EAST_X), n(C.OUTER_ZONE_MIN_X), n(C.OUTER_ZONE_MAX_X)))
print(string.format('PACE speed=%s day=%s view=%sx%s',
  n(C.GAME_SPEED), n(C.DAY_DURATION), n(C.CAMERA_VIEW_WIDTH), n(C.CAMERA_VIEW_HEIGHT)))

local ids = {}
for k, _ in pairs(C.MAP_LANDMARKS) do ids[#ids + 1] = k end
table.sort(ids)
local row = {}
for _, id in ipairs(ids) do
  local lm = C.MAP_LANDMARKS[id]
  row[#row + 1] = string.format('%s@%s%s', id, n(lm.x), lm.reclaimable and ('/' .. lm.reclaimable) or '')
end
print('LANDMARKS ' .. table.concat(row, ' '))

print(string.format('RECLAIM max=%s costP=%s costS=%s secP=%s secS=%s yieldP=%s yieldS=%s',
  n(C.RECLAIM.MAX_LEVEL), n(C.RECLAIM.COST.PADDY), n(C.RECLAIM.COST.SALT),
  n(C.RECLAIM.SECONDS.PADDY), n(C.RECLAIM.SECONDS.SALT),
  n(C.RECLAIM.PADDY_YIELD_PER_LEVEL), n(C.RECLAIM.SALT_YIELD_PER_LEVEL)))

local zs = {}
for _, z in ipairs(C.FOG_ZONES) do
  zs[#zs + 1] = string.format('%s(x=%s w=%s start=%s)', z.id, n(z.x), n(z.width), z.startRevealed and 'lit' or 'dark')
end
print('FOG r=' .. n(C.FOG_REVEAL_RADIUS) .. ' ' .. table.concat(zs, ' '))

local hs = {}
for _, hx in ipairs(C.HOUSE_SLOTS) do hs[#hs + 1] = tostring(hx.x or hx) end
print('HOUSE_SLOTS ' .. table.concat(hs, ','))

local ts = {}
for _, t in ipairs(C.TOWER_SLOTS) do ts[#ts + 1] = t.id end
print('TOWER_SLOTS ' .. table.concat(ts, ','))

print(string.format('GATE innerHp=%s innerMaxLv=%s innerCost=%s innerDefX=%s eastDefX=%s',
  n(C.INNER_GATE_BASE_HP), n(C.INNER_GATE_MAX_LEVEL), n(C.INNER_GATE_UPGRADE_COST),
  n(C.INNER_GATE_DEFENSE_X), n(C.EAST_GATE_DEFENSE_X)))
