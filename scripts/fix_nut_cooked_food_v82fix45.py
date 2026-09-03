#!/usr/bin/env python3
"""v82-fix45: 修正 v82-fix42 的 food 字段错误

v82-fix42 时 food 误写为 L3 类目名「熟制坚果及籽类（带壳、脱壳、包衣）」。
用户指出应该是 L2 参考行的原始 food 名：
  - 铅 Pb → food='生咖啡豆及烘焙咖啡豆'
  - 镉 Cd → food='花生'
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

L3_NAME = "熟制坚果及籽类（带壳、脱壳、包衣）"

food_map = {"Pb": "生咖啡豆及烘焙咖啡豆", "Cd": "花生"}

fixed_count = 0
for c in data["contaminants"]:
    sym = c.get("symbol", "")
    if sym not in food_map:
        continue
    new_food = food_map[sym]
    for it in c.get("items", []):
        if it.get("a1_l3") == L3_NAME and it.get("food") == L3_NAME:
            old = it["food"]
            it["food"] = new_food
            print(f"{sym} (id={it.get('id')}): food {old!r} → {new_food!r}")
            fixed_count += 1

print(f"Fixed {fixed_count} rows")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix44-beverage-no-new-tree-2026-09-01"
NEW_META = "v82-fix45-nut-cooked-food-fix-2026-09-01"
OLD_TITLE = "[v82-fix44]"
NEW_TITLE = "[v82-fix45]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")