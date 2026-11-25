-- 只列出「地平线以下」(水面区) 的节点，用来查倒影/水面附近到底挂了什么。
local lines = {}
local function walk(n, d, nx, ny)
	local x, y = nx, ny
	local tx, ty = 0, 0
	pcall(function()
		tx = n.x
		ty = n.y
	end)
	x, y = nx + tx, ny + ty
	local sz = nil
	pcall(function()
		sz = n.size
	end)
	if y < 120 and sz and math.abs(sz.width) > 50 then
		lines[#lines + 1] = string.format(
			'LOW %s d=%d pos %.0f,%.0f size %.0fx%.0f tag=%s vis=%s op=%.2f',
			n.__classname or '?',
			d,
			x,
			y,
			sz.width,
			sz.height,
			tostring(n.tag),
			tostring(n.visible),
			n.opacity or -1
		)
	end
	local ch = n.children
	if ch then
		for i = 1, #ch do
			walk(ch[i], d + 1, x, y)
		end
	end
end
walk(Director.entry, 0, 0, 0)
print('LOWCOUNT ' .. #lines)
for i = 1, #lines do
	print(lines[i])
end
