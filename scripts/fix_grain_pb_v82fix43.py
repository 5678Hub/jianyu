#!/usr/bin/env python3
"""v82-fix43: 谷物及其制品 L1 类别最终修订

用户反馈：L3 小麦粉（包括食用麸皮）显示「铅 Pb 糙米、大米、小麦粉、玉米糁等 ≤0.2」，
food 字段「糙米、大米、小麦粉、玉米糁等」不在 PDF 表 1 中。
PDF 表 1 谷物及其制品铅条目：
  - 谷物及其制品*〔麦片、面筋、粥类罐头、带馅(料)面米制品除外〕: 0.2
  - 麦片、面筋、粥类罐头、带馅(料)面米制品: 0.5

要求：制修订谷物及其制品（不包括焙烤制品）整个 L1 类别，其他类别不动。

问题与修复：
1. Pb idx=64-67: food='糙米、大米、小麦粉、玉米糁等' 不在 PDF
   → 改为各 L3/L4 自身的类目名
2. Pb idx=68: a1_l2='谷物制品' 错位（food 含麦片，但麦片属 L2 谷物碾磨加工品）
   → 改为 L1 own row（a1_l2/l3/l4 全空），与 PDF 中 0.5 条目作为 0.2 排除项的并列行对齐
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

L1 = "谷物及其制品（不包括焙烤制品）"
L2_MILL = "谷物碾磨加工品"

lead = next((c for c in data["contaminants"] if c.get("symbol") == "Pb"), None)
if lead is None:
    sys.exit("ERROR: lead contaminant block not found")

items = lead["items"]
changes = []

# 1) Pb idx=64-67: food 改为 L3/L4 类目名
food_map = {
    "糙米（包括色稻米）": "糙米（包括色稻米）",
    "大米（粉）": "大米（粉）",
    "小麦粉（包括食用麸皮）": "小麦粉（包括食用麸皮）",
    "玉米粉、玉米糁（渣）": "玉米粉、玉米糁（渣）",
}
for i, it in enumerate(items):
    if it.get("a1_l1") != L1:
        continue
    if it.get("a1_l2") != L2_MILL:
        continue
    l3 = it.get("a1_l3", "")
    if l3 in food_map and it.get("food") == "糙米、大米、小麦粉、玉米粉、玉米糁等":
        old_food = it["food"]
        it["food"] = food_map[l3]
        changes.append(f"idx={i} food: {old_food!r} → {it['food']!r}")

# 2) Pb idx=68: a1_l2 错位，移为 L1 own row
for i, it in enumerate(items):
    if (it.get("a1_l1") == L1
        and it.get("food") == "麦片、面筋、粥类罐头、带馅料面米制品"):
        old_l2 = it.get("a1_l2", "")
        old_l3 = it.get("a1_l3", "")
        old_l4 = it.get("a1_l4", "")
        it["a1_l2"] = ""
        it["a1_l3"] = ""
        it["a1_l4"] = ""
        changes.append(f"idx={i} a1_l*: [{old_l2}][{old_l3}][{old_l4}] → [][ ]")

for c in changes:
    print(c)

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix42-nut-cooked-pb-cd-2026-09-01"
NEW_META = "v82-fix43-grain-pb-food-name-2026-09-01"
OLD_TITLE = "[v82-fix42]"
NEW_TITLE = "[v82-fix43]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")