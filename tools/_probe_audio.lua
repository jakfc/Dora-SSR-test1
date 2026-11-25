-- 音频接入自检：确认每个音频文件在运行时找得到，并能真的开播（返回 handler）
local sfx = {
	'sword_slash', 'arrow_shoot', 'arrow_hit', 'cannon_fire', 'cannon_hit',
	'qilin_punch', 'shockwave', 'hurt', 'enemy_die', 'coin_silver',
	'build_hammer', 'farm_hoe', 'upgrade', 'recruit', 'drum_rally',
	'gate_open', 'wave_horn', 'ui_click', 'ui_hover',
}
local bgm = { 'title', 'day', 'night', 'victory', 'defeat' }
local bad = 0
for i = 1, #sfx do
	local f = 'assets/audio/sfx/sfx_' .. sfx[i] .. '.wav'
	local ex = Content.exist(f)
	local h = -1
	if ex then h = Audio:play(f, false) end
	if h < 0 then bad = bad + 1 end
	print(string.format('SFX %-14s exist=%-5s handler=%d', sfx[i], tostring(ex), h))
end
for i = 1, #bgm do
	local f = 'assets/audio/bgm/bgm_' .. bgm[i] .. '.wav'
	local ex = Content.exist(f)
	print(string.format('BGM %-14s exist=%-5s', bgm[i], tostring(ex)))
end
print(string.format('MISSING_FILE_TEST exist=%s', tostring(Content.exist('assets/audio/sfx/sfx_no_such.wav'))))
print(string.format('VOLUME %.2f  BAD=%d', Audio.volume, bad))
