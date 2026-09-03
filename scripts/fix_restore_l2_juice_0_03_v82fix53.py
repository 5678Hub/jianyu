#!/usr/bin/env python3
"""v82-fix53: 恢复 L2 果蔬汁类及其饮料 own row 0.03

用户截图 spec:
  铅 Pb 果蔬汁类及其饮料〔含浆果及小粒水果的果蔬汁类及其饮料、浓缩果蔬汁(浆)除外〕 ≤0.03 mg/kg mg/kg GB 5009.12
  「增加到L2级果蔬汁类及其饮料...使L2果蔬汁类及其饮料有两条限量内容」

副作用: walkExact Fallback B 会让 L2 own row 也注册到 L3 浓缩果蔬汁（浆）下
  → L3 浓缩果蔬汁（浆）会显示 2 条 row（0.5 own + 0.03 fallback）
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

# 检查是否已存在
exists = False
for it in items:
    if (it.get("a1_l1") == "饮料类"
        and it.get("a1_l2", "").startswith("果蔬汁类及其饮料")
        and it.get("a1_l3") == ""
        and it.get("limit_value") == "0.03"):
        exists = True
        print(f"Already exists, skip insert")
        break

if not exists:
    new_row = {
        "id": "r0005",
        "a1_l1": "饮料类",
        "a1_l2": "果蔬汁类及其饮料（例如：苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等）",
        "a1_l3": "",
        "a1_l4": "",
        "food": "果蔬汁类及其饮料〔含浆果及小粒水果的果蔬汁类及其饮料、浓缩果蔬汁(浆)除外〕",
        "limit_value": "0.03",
        "unit": "mg/kg",
        "has_limit": True,
        "inspection_method": "GB 5009.12",
        "note": "",
        "modif": "",
        "sub_value": "",
        "pollutant": "铅",
    }
    # 找到 r0003 (L2 0.05) 之前插入
    insert_pos = None
    for i, it in enumerate(items):
        if it.get("id") == "r0003":
            insert_pos = i
            break
    if insert_pos is None:
        items.append(new_row)
        print(f"Appended at end")
    else:
        items.insert(insert_pos, new_row)
        print(f"Inserted at pos {insert_pos} (before r0003): L2 0.03 own row")
        print(f"  food={new_row['food']}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix52-simplify-r0003-food-2026-09-01"
NEW_META = "v82-fix53-restore-l2-juice-0-03-2026-09-01"
OLD_TITLE = "[v82-fix52]"
NEW_TITLE = "[v82-fix53]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")