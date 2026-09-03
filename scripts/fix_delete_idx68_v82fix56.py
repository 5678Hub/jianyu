#!/usr/bin/env python3
"""v82-fix56: 删 idx=68 (Pb L1 谷物 own 0.5 row)

用户反馈: 「只保留63这是对的」
- idx=63 (Pb 0.2 谷物〔...除外〕) 保留 ✓
- idx=68 (Pb 0.5 麦片、面筋、粥类罐头、带馅料面米制品) 删除
  v82-fix43 自作主张加的,不在用户最初 spec
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

# 删 idx=68
removed = []
new_items = []
for i, it in enumerate(items):
    if (it.get("a1_l1") == "谷物及其制品（不包括焙烤制品）"
        and it.get("a1_l2", "") == ""
        and it.get("a1_l3", "") == ""
        and it.get("limit_value") == "0.5"
        and it.get("food", "") == "麦片、面筋、粥类罐头、带馅料面米制品"):
        removed.append(i)
        print(f"[DELETE] idx={i} (Pb L1 own 0.5 麦片/面筋/粥类罐头/带馅料面米制品 row)")
        print(f"  food: {it.get('food','')!r}")
        continue
    new_items.append(it)
items[:] = new_items
print(f"Removed idx={removed}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix55-batch-normalize-6-notes-2026-09-02"
NEW_META = "v82-fix56-delete-idx68-grain-l1-0-5-2026-09-02"
OLD_TITLE = "[v82-fix55]"
NEW_TITLE = "[v82-fix56]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")