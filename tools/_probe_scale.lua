-- 核对「美术素材 vs 人」的在运行尺寸：把带 tag 的挂点（tag 就是 Assets.ts 里的素材 id）连同
-- 它实际绘制的宽高一起打出来。人的高度以 villager 为基准（1 人 = 50 设计像素）。
-- 配合 tools/inspect_scene.py 用（把 dump_scene.lua 临时换成这个，或直接 cli agent command）。
local out = {}
local function num(v)
	if type(v) == 'number' then return v end
	return 0
end

local function selfSize(n)
	local w, h = 0, 0
	pcall(function()
		if n.size then w = num(n.size.width); h = num(n.size.height) end
	end)
	return w, h
end

local function kidMax(n)
	local w, h, best = 0, 0, 0
	local ch = n.children
	if ch then
		for i = 1, #ch do
			local cw, chh = selfSize(ch[i])
			if chh > best then best = chh; w, h = cw, chh end
		end
	end
	return w, h, best
end

local function walk(n, d, ax, ay)
	if d > 30 then return end
	local nx, ny = ax + num(n.x), ay + num(n.y)
	local tag = ''
	pcall(function() tag = n.tag or '' end)
	if tag ~= '' then
		local ow, oh = selfSize(n)
		local kw, kh = kidMax(n)
		local kids = 0
		pcall(function() if n.children then kids = #n.children end end)
		out[#out + 1] = string.format(
			'TAG %-28s pos %.0f,%.0f 自己 %.1fx%.1f 子 %.1fx%.1f 子数 %d',
			tag, nx, ny, ow, oh, kw, kh, kids)
	end
	local ch = n.children
	if ch then
		for i = 1, #ch do walk(ch[i], d + 1, nx, ny) end
	end
end

walk(Director.entry, 0, 0, 0)
print('TAGCOUNT ' .. #out)
for i = 1, #out do print(out[i]) end
