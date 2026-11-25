-- 打印可视区域/缩放与关键精灵的实际绘制尺寸（看画质是否被放大糊掉）
local ok, v = pcall(function() return View.size end)
if ok and v then
	print(string.format('VIEW %.1f x %.1f', v.width, v.height))
end
local okc, cam = pcall(function() return Director.currentCamera end)
if okc and cam then
	local okz, z = pcall(function() return cam.zoom end)
	if okz then print(string.format('CAMZOOM %.3f', z)) end
end
local n = 0
local function walk(node, ax, ay)
	if n > 90 then return end
	local nx, ny = ax + (node.x or 0), ay + (node.y or 0)
	local okt, tex = pcall(function() return node.texture end)
	if okt and tex then
		local tw, th, sw, sh = 0, 0, 0, 0
		pcall(function() tw = tex.width; th = tex.height end)
		pcall(function() sw = node.size.width; sh = node.size.height end)
		if sw > 8 and sh > 8 then
			n = n + 1
			print(string.format('SPR tex %dx%d draw %.1fx%.1f ratio %.2f pos %.0f,%.0f',
				tw, th, sw, sh, th / math.max(1, sh), nx, ny))
		end
	end
	local ch = node.children
	if ch then for i = 1, #ch do walk(ch[i], nx, ny) end end
end
walk(Director.entry, 0, 0)
print('DONE ' .. n)
