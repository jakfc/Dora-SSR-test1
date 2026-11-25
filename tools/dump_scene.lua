-- 在游戏运行中把整个场景树倒出来（精灵尺寸/位置 + 文字），用来核对美术接入是否生效。
-- 配合 tools/inspect_scene.py 使用，见 tools/README-inspect.md。
local lines = {}
-- 先记录可视区/镜头缩放，便于核对「镜头拉近」与 UI 空间
pcall(function()
	lines[#lines + 1] = string.format('VIEW %.1f x %.1f', View.size.width, View.size.height)
end)
pcall(function()
	local cam = Director.currentCamera
	lines[#lines + 1] = string.format('CAMZOOM %.3f  campos %.1f,%.1f', cam.zoom, cam.position.x, cam.position.y)
end)
local function walk(n, d, ax, ay)
	if d > 30 then return end
	local nx, ny = ax + (n.x or 0), ay + (n.y or 0)
	local ok, tex = pcall(function() return n.texture end)
	if ok and tex then
		local tw, th, sw, sh, sx, sy, op, vis, tg = 0, 0, 0, 0, 1, 1, 1, true, ''
		pcall(function() tw = tex.width; th = tex.height end)
		pcall(function() sw = n.size.width; sh = n.size.height end)
		pcall(function() sx = n.scaleX; sy = n.scaleY; op = n.opacity; vis = n.visible end)
		pcall(function() tg = n.tag end)
		lines[#lines + 1] = string.format(
			'SPR tex %dx%d  draw %.1fx%.1f  pos %.0f,%.0f  scaleX %.2f  scaleY %.2f  op %.2f  vis %s  tag %s',
			tw, th, sw, sh, nx, ny, sx, sy, op, tostring(vis), tostring(tg))
	end
	local ok2, txt = pcall(function() return n.text end)
	if ok2 and type(txt) == 'string' and #txt > 0 and #txt < 70 then
		lines[#lines + 1] = string.format('LBL "%s"  pos %.0f,%.0f', txt, nx, ny)
	end
	local ch = n.children
	if ch then
		for i = 1, #ch do walk(ch[i], d + 1, nx, ny) end
	end
end
walk(Director.entry, 0, 0, 0)
print('COUNT ' .. #lines)
for i = 1, #lines do print(lines[i]) end
