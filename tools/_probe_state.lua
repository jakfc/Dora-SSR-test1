local GS = require('src.config.GameState')
local gs = GS.GameState.instance
local before = gs:donationOf('PROBE')
gs:addDonation('PROBE', 100)
local mid = gs:donationOf('PROBE')
gs:clearDonation('PROBE')
print('DONATION before=' .. before .. ' after=' .. mid .. ' cleared=' .. gs:donationOf('PROBE'))
print('food=' .. gs.food .. ' foodCap=' .. gs.foodCapacity .. ' silver=' .. gs.silver .. ' pop=' .. gs.populationCount)
print('moraleBonus=' .. gs.moraleBonus .. ' moraleHpBonus=' .. gs.moraleHpBonus)
