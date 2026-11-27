-- 探针：验证逐帧显示倍率 —— 同一角色 idle 与 attack 在屏幕上的显示高应一致
local A = require('src.config.Assets')
local found = {}
local function walk(node)
  if node == nil then return end
  local tag = node.tag
  if type(tag) == 'string' and tag:sub(1, 5) == 'anim|' and #found < 8 then
    found[#found + 1] = node
  end
  local kids = node.children
  if kids ~= nil then
    for i = 1, #kids do walk(kids[i]) end
  end
end
walk(Director.entry)
print('HOLDERS ' .. #found)
local function visibleSize(n)
  local kids = n.children
  if kids == nil then return nil end
  for i = 1, #kids do
    local s = kids[i]
    if s.visible and s.size ~= nil then
      return string.format('%.1fx%.1f', s.size.width, s.size.height), s.tag
    end
  end
  return nil, '-'
end
for i = 1, #found do
  local n = found[i]
  local style, prefix = n.tag:match('^anim|([^|]+)|([^|]+)|')
  local sz, tag = visibleSize(n)
  print(string.format('%d %s prefix=%s 当前=%s(tag %s)', i, tostring(style), tostring(prefix), tostring(sz), tostring(tag)))
  if style ~= nil then
    for _, act in ipairs({'attack', 'walk', 'qilin', 'hurt'}) do
      local cnt = A.artAnimCount(style, act)
      if cnt > 0 then
        A.artAnimInto(n, style, act, 0)
        local s2 = visibleSize(n)
        print(string.format('    ->%s(%d帧) %s', act, cnt, tostring(s2)))
      end
    end
    -- 复位成 idle/原前缀
    if A.artAnimCount(style, prefix) > 0 then A.artAnimInto(n, style, prefix, 0) end
  end
end
