--[[
mdpdf.lua: layout fixes applied to every document mdpdf converts (LaTeX output only).
Works on pandoc 2.17 (the image) and 3.x.

1. Breakable inline code. LaTeX cannot break \texttt except at hyphens, so a long path
   such as `uai-infra/terraform/modules/aws/ecs/main.tf:438-556` runs into the next table
   column or off the page. Inline code is written as \texttt with \allowbreak after
   / . : _ , - = ( and every 16 characters of an unbroken run (digests). Code inside
   headings is left alone: commands there break the PDF bookmarks.
2. Headings stay with what follows: \needspace (mdpdf-core.tex) before every heading.
3. Table column widths. pandoc takes widths from the separator row's dashes, so
   `|---|---|---|` gives every column the same width. When all widths are equal (or
   default), they are set from the content instead: the mean cell length, with a floor
   so the column's longest ordinary word fits. Unequal dashes are the author's choice
   and are kept.
4. Landscape figures. An image with class `landscape` (mdpdf adds it to a mermaid block
   that contains `%% mdpdf: landscape`) goes on a landscape page of its own, queued with
   \afterpage so the text keeps filling the current page. A paragraph right after it
   that starts with "Figure" or "Fig." is its caption and moves with it; otherwise the
   alt text is the caption.
]]

if not FORMAT:match("latex") then
  return {}
end

-- 1. Inline code -----------------------------------------------------------------

local ESCAPES = {
  ["\\"] = "\\textbackslash{}", ["{"] = "\\{", ["}"] = "\\}", ["_"] = "\\_",
  ["#"] = "\\#", ["%"] = "\\%", ["&"] = "\\&", ["$"] = "\\$",
  ["~"] = "\\textasciitilde{}", ["^"] = "\\textasciicircum{}",
}
local BREAK_AFTER = { ["/"] = true, ["."] = true, [":"] = true, ["_"] = true,
  [","] = true, ["-"] = true, ["="] = true, ["("] = true }
local RUN = 16

local function breakable_tt(text)
  local out, run = {}, 0
  local n = #text
  for i = 1, n do
    local ch = text:sub(i, i)
    out[#out + 1] = ESCAPES[ch] or ch
    if ch:match("%w") then run = run + 1 else run = 0 end
    if i < n and (BREAK_AFTER[ch] or (run > 0 and run % RUN == 0)) then
      out[#out + 1] = "\\allowbreak{}"
    end
  end
  return "\\texttt{" .. table.concat(out) .. "}"
end

local KEEP = "mdpdf-keep"

local mark_heading_code = {
  Header = function(el)
    return el:walk({
      Code = function(c)
        c.classes:insert(KEEP)
        return c
      end,
    })
  end,
}

local inline_code = {
  Code = function(el)
    if el.classes:includes(KEEP) then
      el.classes = el.classes:filter(function(c) return c ~= KEEP end)
      return el
    end
    return pandoc.RawInline("latex", breakable_tt(el.text))
  end,
}

-- 2. Headings ----------------------------------------------------------------------

local keep_headings = {
  Header = function(el)
    return { pandoc.RawBlock("latex", "\\needspace{8\\baselineskip}"), el }
  end,
}

-- 3. Table widths -------------------------------------------------------------------

local CHAR_IN = 0.07    -- inches per character at the table font (\footnotesize Noto Sans)
local PAD_IN = 0.12     -- cell padding
local TEXT_IN = 6.5     -- text width at 1in margins on Letter
local MIN_FRAC = 0.07
local MAX_WORD = 20     -- longer tokens (UUIDs, paths) break anyway

local function cells_of(row)
  return row.cells or row[2]
end

local function contents_of(cell)
  return cell.contents or cell[5]
end

local function cell_text(cell)
  return pandoc.utils.stringify(pandoc.Div(contents_of(cell)))
end

local function longest_plain_word(cell)
  local longest = 0
  pandoc.Div(contents_of(cell)):walk({
    Str = function(s)
      local len = utf8.len(s.text) or #s.text
      if len > longest then longest = len end
    end,
  })
  return longest
end

local function body_rows(tbl)
  local rows = {}
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body or body[4]) do rows[#rows + 1] = row end
  end
  return rows
end

local function width_of(colspec)
  local w = colspec.width or colspec[2]
  if type(w) == "number" then return w end
  return nil
end

local function set_width(tbl, i, w)
  local cs = tbl.colspecs[i]
  if cs.width ~= nil or cs.alignment ~= nil then
    cs.width = w
  else
    cs[2] = w
  end
  tbl.colspecs[i] = cs
end

local function widths_are_unset_or_equal(tbl)
  local first = width_of(tbl.colspecs[1])
  for i = 2, #tbl.colspecs do
    local w = width_of(tbl.colspecs[i])
    if (w == nil) ~= (first == nil) then return false end
    if w ~= nil and math.abs(w - first) > 0.002 then return false end
  end
  return true
end

local table_widths = {
  Table = function(tbl)
    local n = #tbl.colspecs
    if n < 2 or not widths_are_unset_or_equal(tbl) then return nil end
    local rows = body_rows(tbl)
    if #rows == 0 then return nil end
    local head_rows = tbl.head.rows or tbl.head[2] or {}

    local means, floors = {}, {}
    for k = 1, n do
      local total, count, word = 0, 0, 3
      for _, row in ipairs(rows) do
        local cell = cells_of(row)[k]
        if cell then
          local len = utf8.len(cell_text(cell)) or 0
          if len > 0 then total = total + len; count = count + 1 end
          word = math.max(word, longest_plain_word(cell))
        end
      end
      for _, row in ipairs(head_rows) do
        local cell = cells_of(row)[k]
        if cell then word = math.max(word, longest_plain_word(cell)) end
      end
      local mean = count > 0 and total / count or 0
      means[k] = math.max(5, math.min(mean, 70))
      floors[k] = math.max(MIN_FRAC, (math.min(word, MAX_WORD) * CHAR_IN + PAD_IN) / TEXT_IN)
    end

    local sum = 0
    for k = 1, n do sum = sum + means[k] end
    local frac = {}
    for k = 1, n do frac[k] = means[k] / sum end

    -- Raise any column below its floor, taking the room from the others in proportion.
    for _ = 1, 5 do
      local fixed, room = {}, 1
      for k = 1, n do
        if frac[k] < floors[k] then fixed[k] = true end
      end
      if next(fixed) == nil then break end
      local free_sum = 0
      for k = 1, n do
        if fixed[k] then frac[k] = floors[k]; room = room - floors[k]
        else free_sum = free_sum + frac[k] end
      end
      if room <= 0 or free_sum <= 0 then break end
      for k = 1, n do
        if not fixed[k] then frac[k] = frac[k] / free_sum * room end
      end
    end

    for k = 1, n do set_width(tbl, k, frac[k]) end
    return tbl
  end,
}

-- 4. Landscape figures ---------------------------------------------------------------

local function landscape_image(block)
  -- pandoc 3: Figure{ Plain{ Image } }; pandoc 2: Para{ Image } (implicit figure).
  -- Not a bare Plain: on pandoc 3 that is the inside of a Figure, and matching it there
  -- would rewrite the figure's content instead of replacing the figure.
  local inlines
  if block.t == "Figure" then
    local inner = block.content[1]
    if inner and (inner.t == "Plain" or inner.t == "Para") then inlines = inner.content end
  elseif block.t == "Para" then
    inlines = block.content
  end
  if not inlines or #inlines ~= 1 or inlines[1].t ~= "Image" then return nil end
  local img = inlines[1]
  if img.classes:includes("landscape") then return img end
  return nil
end

local function is_caption(block)
  if not block or block.t ~= "Para" then return false end
  local first = block.content[1]
  return first and first.t == "Str" and (first.text == "Figure" or first.text == "Fig.")
end

local landscape_figures = {
  Blocks = function(blocks)
    local out = pandoc.List()
    local i = 1
    while i <= #blocks do
      local img = landscape_image(blocks[i])
      if img then
        local caption
        if is_caption(blocks[i + 1]) then
          caption = blocks[i + 1].content
          i = i + 1
        else
          caption = img.caption or img.content
        end
        out:insert(pandoc.RawBlock("latex",
          "\\afterpage{\\begin{landscape}\\centering\n" ..
          "\\includegraphics[width=\\linewidth,height=0.86\\textheight,keepaspectratio]{" ..
          img.src .. "}\\par\\medskip\n\\begin{minipage}{\\linewidth}\\raggedright"))
        out:insert(pandoc.Plain(caption))
        out:insert(pandoc.RawBlock("latex", "\\end{minipage}\n\\end{landscape}}"))
      else
        out:insert(blocks[i])
      end
      i = i + 1
    end
    return out
  end,
}

-- Table widths are measured before inline code becomes raw LaTeX (stringify cannot see it).
return { table_widths, mark_heading_code, landscape_figures, inline_code, keep_headings }
