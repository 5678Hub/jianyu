#!/usr/bin/env python3
"""v82-fix44: 撤销 v82-fix41 新增的 tree 节点，改用现有 L2/L3 节点 + 截图 food 格式

用户说：「不要新增」（tree 节点）
数据按截图格式重新组织:
  - L2 果蔬汁类及其饮料:
    - 0.03 row (food='饮料类：果蔬汁类及其饮料[含浆果及小粒水果的果蔬汁类及其饮料、浓缩果蔬汁(浆)除外]')
    - 0.05 row (food='饮料类：果蔬汁类及其饮料：含浆果及小粒水果的果蔬汁类及其饮料(葡萄汁除外)')
  - L3 果蔬汁（浆）:
    - 0.04 row (food='饮料类：果蔬汁类及其饮料：含浆果及小粒水果的果蔬汁类及其饮料：葡萄汁')

撤销:
  - tree 删除 catid=196 含浆果及小粒水果的果蔬汁类及其饮料（葡萄汁除外）
  - tree 删除 catid=197 葡萄汁
  - Pb idx=86 (含浆果... 0.05) 删除
  - Pb idx=87 (葡萄汁 0.04) 删除

新增/修改:
  - Pb idx=85 food 更新为截图格式 (保留为 L2 own row, a1_l3='', a1_l4='')
  - 新增 Pb row at L2 果蔬汁类及其饮料 (a1_l3=''): 0.05
  - 新增 Pb row at L3 果蔬汁（浆）: 0.04
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

L1 = "饮料类"
L2 = "果蔬汁类及其饮料（例如：苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等）"
L3_ZHI = "果蔬汁（浆）"

lead = next((c for c in data["contaminants"] if c.get("symbol") == "Pb"), None)
if lead is None:
    sys.exit("ERROR: lead contaminant block not found")

# 1) tree 删除 catid=196/197（v82-fix41 新增的含浆果.../葡萄汁节点）
tree = data["appendix_a1"]["tree"]
removed_tree_count = 0
for n1 in tree:
    if n1.get("name") != L1:
        continue
    for c in n1.get("children", []):
        if c.get("name") != L2:
            continue
        before = len(c.get("children", []))
        c["children"] = [k for k in c.get("children", []) if k.get("catid") not in (196, 197)]
        removed_tree_count = before - len(c["children"])
        print(f"Removed {removed_tree_count} tree nodes from 果蔬汁类及其饮料")
        break
    break
if removed_tree_count != 2:
    print(f"WARN: expected to remove 2 tree nodes, removed {removed_tree_count}")

# 2) Pb items 删除 idx=86/87（v82-fix41 新增的 0.05/0.04 rows）
items = lead["items"]
removed_items = []
new_items = []
for i, it in enumerate(items):
    if it.get("a1_l3") == "含浆果及小粒水果的果蔬汁类及其饮料（葡萄汁除外）":
        removed_items.append(i)
        continue
    new_items.append(it)
items[:] = new_items
print(f"Removed Pb items at: {removed_items}")

# 3) Pb idx=85（原 L2 own row 0.03）food 更新为截图格式
for i, it in enumerate(items):
    if (it.get("a1_l1") == L1 and it.get("a1_l2") == L2
        and it.get("a1_l3") == "" and it.get("limit_value") == "0.03"):
        old_food = it["food"]
        it["food"] = "饮料类：果蔬汁类及其饮料[含浆果及小粒水果的果蔬汁类及其饮料、浓缩果蔬汁(浆)除外]"
        it["note"] = "以Pb计。含浆果及小粒水果的果蔬汁类及其饮料、浓缩果蔬汁(浆)除外。"
        it["inspection_method"] = "按GB 5009.12规定的方法测定。"
        print(f"Updated Pb idx={i} food: {old_food!r} → {it['food']!r}")
        break

# 4) 新增 Pb row at L2 果蔬汁类及其饮料 (a1_l3=''): 0.05
# 5) 新增 Pb row at L3 果蔬汁（浆）: 0.04
# 分配 r id
max_idx = 0
def walk_max_idx(node):
    global max_idx
    if isinstance(node, dict):
        if isinstance(node.get("id"), str) and node["id"].startswith("r"):
            try:
                n = int(node["id"][1:])
                if n > max_idx: max_idx = n
            except ValueError:
                pass
        for v in node.values():
            walk_max_idx(v)
    elif isinstance(node, list):
        for v in node:
            walk_max_idx(v)
walk_max_idx(data)
print(f"Max r-id in data: r{max_idx:04d}")

new_l2_row = {
    "id": f"r{max_idx + 1:04d}",
    "food": "饮料类：果蔬汁类及其饮料：含浆果及小粒水果的果蔬汁类及其饮料(葡萄汁除外)",
    "pollutant": "铅",
    "limit_value": "0.05",
    "has_limit": True,
    "sub_value": "",
    "unit": "mg/kg",
    "note": "以Pb计。仅限含浆果及小粒水果的果蔬汁类及其饮料(葡萄汁除外)。",
    "modif": "",
    "inspection_method": "按GB 5009.12规定的方法测定。",
    "a1_l1": L1, "a1_l2": L2, "a1_l3": "", "a1_l4": "",
}
items.append(new_l2_row)
print(f"Added L2 row 0.05: id={new_l2_row['id']}, food={new_l2_row['food']}")

new_l3_row = {
    "id": f"r{max_idx + 2:04d}",
    "food": "饮料类：果蔬汁类及其饮料：含浆果及小粒水果的果蔬汁类及其饮料：葡萄汁",
    "pollutant": "铅",
    "limit_value": "0.04",
    "has_limit": True,
    "sub_value": "",
    "unit": "mg/kg",
    "note": "以Pb计。仅限葡萄汁。",
    "modif": "",
    "inspection_method": "按GB 5009.12规定的方法测定。",
    "a1_l1": L1, "a1_l2": L2, "a1_l3": L3_ZHI, "a1_l4": "",
}
items.append(new_l3_row)
print(f"Added L3 果蔬汁（浆） row 0.04: id={new_l3_row['id']}, food={new_l3_row['food']}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix43-grain-pb-food-name-2026-09-01"
NEW_META = "v82-fix44-beverage-no-new-tree-2026-09-01"
OLD_TITLE = "[v82-fix43]"
NEW_TITLE = "[v82-fix44]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")