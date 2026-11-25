local GS = require('src.config.GameState')
local GC = require('src.config.GameConfig')
local gs = GS.GameState.instance
local lv0 = gs.ancestralHallLevel
gs.ancestralHallLevel = 3
print(string.format('MORALE lv=%d atk=%.3f hp=%.3f (expect atk=%.3f hp=%.3f)',
  gs.ancestralHallLevel, gs.moraleBonus, gs.moraleHpBonus,
  2 * GC.GameConfig.MORALE_ATTACK_PER_LEVEL, 2 * GC.GameConfig.MORALE_HP_PER_LEVEL))
gs.ancestralHallLevel = lv0
print(string.format('ECON food=%d foodCap=%d housing=%d pop=%d houses=%d foodPerPerson=%d',
  gs.food, gs.foodCapacity, gs.housingCapacity, gs.populationCount, #gs.houses, GC.GameConfig.FOOD_PER_PERSON))
print(string.format('BRIBE scout=%d samurai=%d boss=%d stun=%.1f retreat=%.1f',
  GC.GameConfig.BRIBE_COST.SCOUT, GC.GameConfig.BRIBE_COST.SAMURAI, GC.GameConfig.BRIBE_COST.BOSS,
  GC.GameConfig.BRIBE_BOSS_STUN_SECONDS, GC.GameConfig.BRIBE_RETREAT_SECONDS))
