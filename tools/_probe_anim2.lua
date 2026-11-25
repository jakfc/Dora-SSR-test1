local lines = {}
local function walk(node)
  if node == nil then return end
  local tag = node.tag
  if type(tag) == 'string' and tag:sub(1, 5) == 'anim|' then
    local kids = node.children
    if kids ~= nil then
      for i = 1, #kids do
        if kids[i].visible then lines[#lines + 1] = tag .. ' -> #' .. i end
      end
    end
  end
  local k = node.children
  if k ~= nil then for i = 1, #k do walk(k[i]) end end
end
walk(Director.entry)
print('FRAMES ' .. table.concat(lines, ' , '))
