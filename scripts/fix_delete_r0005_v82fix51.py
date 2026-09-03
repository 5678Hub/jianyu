#!/usr/bin/env python3
"""v82-fix51: 删 r0005 (L2 果蔬汁类 0.03 own row)

用户指示: L3 浓缩果蔬汁（浆）只保留 0.5 这一条
副作用: walkExact Fallback B 会让 L2 own row 也注册到 L3 浓缩果蔬汁（浆）下
解决: 删 L2 own row 0.03 (r0005) → L3 浓缩果蔬汁（浆）下只剩 0.5 own row

代价: PDF 表 1 中 L2 果蔬汁类及其饮料 own 应是 0.03 缺失 → L2 果蔬汁类本级只剩 r0003 (0.05 含浆果...)
"""
import json
import sys
from pathlib import Path

FILE = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
BACKSLASH = chr(92); QUOTE = chr(34)

html = FILE.read_text(encoding="utf-8")
start_tag = '<script type="application/json" id="inlineData">'
end_tag = '</script>'
start = html.index(start_tag) + len(start_tag)
depth = 0; in_str = False; esc = False; obj_end = -1
for off in range(start, len(html)):
    ch = html[off]
    if in_str:
        if esc: esc = False
        elif ch == BACKSLASH: esc = True
        elif ch == QUOTE: in_str = False
        continue
    if ch == QUOTE: in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = off + 1; break
if obj_end == -1:
    sys.exit("ERROR: inlineData JSON not found")

raw_json = html[start:obj_end]
data = json.loads(raw_json)

pb = next(c for c in data["contaminants"] if c.get("symbol") == "Pb")
items = pb["items"]

# 删 r0005
removed = []
new_items = []
for i, it in enumerate(items):
    if it.get("id") == "r0005":
        removed.append(i)
        print(f"[DELETE] idx={i} r0005 (L2 果蔬汁类 0.03 own row)")
        print(f"  food={it.get('food','')!r}")
        continue
    new_items.append(it)
items[:] = new_items
print(f"Removed idx={removed}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix50-restore-concentrate-juice-0-5-2026-09-01"
NEW_META = "v82-fix51-delete-r0005-keep-concentrate-only-2026-09-01"
OLD_TITLE = "[v82-fix50]"
NEW_TITLE = "[v82-fix51]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")