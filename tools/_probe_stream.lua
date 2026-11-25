local bgm = { 'title', 'day', 'night' }
for i = 1, #bgm do
	local f = 'assets/audio/bgm/bgm_' .. bgm[i] .. '.wav'
	local ok, err = pcall(function() Audio:playStream(f, true, 1.0) end)
	print(string.format('STREAM %-8s ok=%s err=%s', bgm[i], tostring(ok), tostring(err)))
end
print('STOP ok=' .. tostring(pcall(function() Audio:stopStream(0.5) end)))
