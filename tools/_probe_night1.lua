local GS = require('src.config.GameState')
local gs = GS.GameState.instance
gs.dayTimer = 0.2
print(string.format('FORCE day=%d phase=%s timer=%.2f', gs.day, gs.phase, gs.dayTimer))
