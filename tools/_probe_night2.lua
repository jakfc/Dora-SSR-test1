local GS = require('src.config.GameState')
local GC = require('src.config.GameConfig')
local gs = GS.GameState.instance
print(string.format('NIGHT day=%d phase=%s hallHp=%d/%d innerGateHp=%d/%d eastGateHp=%d/%d open=%s',
  gs.day, gs.phase, gs.ancestralHallHp, gs.ancestralHallMaxHp,
  gs.innerGateHp, gs.innerGateMaxHp, gs.eastGateHp, gs.eastGateMaxHp,
  tostring(gs.eastGateOpen)))
print(string.format('HALL morale=%.2f hpBonus=%.2f silver=%d pop=%d',
  gs.moraleBonus, gs.moraleHpBonus, gs.silver, gs.populationCount))
