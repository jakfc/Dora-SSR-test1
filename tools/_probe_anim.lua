local A = require('src.config.Assets')
local found = {}
local function walk(node)
  if node == nil then return end
  local tag = node.tag
  if type(tag) == 'string' and tag:sub(1, 5) == 'anim|' and #found < 4 then
    found[#found + 1] = node
  end
  local kids = node.children
  if kids ~= nil then
    for i = 1, #kids do walk(kids[i]) end
  end
end
walk(Director.entry)
print('FOUND ' .. #found)
for i = 1, #found do
  local n = found[i]
  local g = n:getChildByTag('f1')
  print(string.format('F%d tag=%s vis=%s hash=%d getf1=%s', i, n.tag, tostring(n.visible), #n.children, tostring(g ~= nil)))
  local a, b, c = n.tag:match('^anim|([^|]+)|([^|]+)|(%d+)$')
  print('   parsed style=' .. tostring(a) .. ' prefix=' .. tostring(b) .. ' n=' .. tostring(c))
  if a ~= nil and i == 2 then
    local sp = A.artAnimInto(n, a, b, 0)
    print('   re-invoke sp=' .. tostring(sp) .. ' tagnow=' .. n.tag .. ' hash=' .. tostring(#n.children) .. ' vis=' .. tostring(n.visible))
  end
end
