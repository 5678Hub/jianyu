#!/usr/bin/env python3
"""v82-fix47: 谷物及其制品(不包括焙烤制品) L1/L2 分类完整修订（对照截图照搬）

截图 spec：
- L1 own row (Pb):
    food = 谷物及其制品〔麦片、面筋、粥类罐头、带馅(料)面米制品除外〕
    limit = 0.2
    method = 按GB 5009.12规定的方法测定。
    note = 以Pb计。稻谷以糙米计。麦片、面筋、粥类罐头、带馅(料)面米制品除外。
- L2 谷物 (Cd):
    food = 谷物及其制品：谷物（稻谷除外）
    limit = 0.1
    method = 按GB 5009.15规定的方法测定。
    note = 以Cd计。稻谷除外。
- L2 谷物 (As):
    food = 谷物及其制品：谷物（稻谷除外）
    limit = 0.5
    method = 按GB 5009.11规定的方法测定。
    note = 以As计。稻谷除外。
- L2 谷物 (Cr):
    food = 谷物及其制品：谷物
    limit = 1.0
    method = 按GB 5009.123规定的方法测定。
    note = 以Cr计。稻谷以糙米计。
- L2 谷物碾磨加工品 (Cd):
    food = 谷物及其制品：谷物碾磨加工品〔糙米、大米（粉）除外〕
    limit = 0.1
    method = 按GB 5009.15规定的方法测定。
    note = 以Cd计。糙米、大米（粉）除外。
- L2 谷物碾磨加工品 (As):
    food = 谷物及其制品：谷物碾磨加工品〔糙米、大米（粉）除外〕
    limit = 0.5
    method = 按GB 5009.11规定的方法测定。
    note = 以As计。糙米、大米（粉）除外。
- L2 谷物碾磨加工品 (Cr):
    food = 谷物及其制品：谷物碾磨加工品
    limit = 1.0
    method = 按GB 5009.123规定的方法测定。
    note = 以Cr计。

不动 idx=68（v82-fix43 自作主张加的 0.5 row，不在本次 spec，等用户决定）。
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

# 按 symbol 索引
sym_map = {c.get("symbol"): c for c in data["contaminants"]}

# spec: idx → (contaminant_symbol, condition, new fields)
# condition: (a1_l1_prefix, a1_l2, a1_l3, limit_value)
SPECS = [
    # Pb L1 own row (idx=63)
    ("Pb", "谷物及其制品（不包括焙烤制品）", "", "", "0.2",
     "谷物及其制品〔麦片、面筋、粥类罐头、带馅(料)面米制品除外〕",
     "按GB 5009.12规定的方法测定。",
     "以Pb计。稻谷以糙米计。麦片、面筋、粥类罐头、带馅(料)面米制品除外。"),

    # Cd L2 谷物 own (idx=0)
    ("Cd", "谷物及其制品（不包括焙烤制品）", "谷物", "", "0.1",
     "谷物及其制品：谷物（稻谷除外）",
     "按GB 5009.15规定的方法测定。",
     "以Cd计。稻谷除外。"),

    # Cd L2 谷物碾磨加工品 own (idx=1)
    ("Cd", "谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", "", "0.1",
     "谷物及其制品：谷物碾磨加工品〔糙米、大米（粉）除外〕",
     "按GB 5009.15规定的方法测定。",
     "以Cd计。糙米、大米（粉）除外。"),

    # As L2 谷物 own (idx=35)
    ("As", "谷物及其制品（不包括焙烤制品）", "谷物", "", "0.5",
     "谷物及其制品：谷物（稻谷除外）",
     "按GB 5009.11规定的方法测定。",
     "以As计。稻谷除外。"),

    # As L2 谷物碾磨加工品 own (idx=36)
    ("As", "谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", "", "0.5",
     "谷物及其制品：谷物碾磨加工品〔糙米、大米（粉）除外〕",
     "按GB 5009.11规定的方法测定。",
     "以As计。糙米、大米（粉）除外。"),

    # Cr L2 谷物 own (idx=9)
    ("Cr", "谷物及其制品（不包括焙烤制品）", "谷物", "", "1.0",
     "谷物及其制品：谷物",
     "按GB 5009.123规定的方法测定。",
     "以Cr计。稻谷以糙米计。"),

    # Cr L2 谷物碾磨加工品 own (idx=10)
    ("Cr", "谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", "", "1.0",
     "谷物及其制品：谷物碾磨加工品",
     "按GB 5009.123规定的方法测定。",
     "以Cr计。"),
]

updated_count = 0
for sym, a1_l1, a1_l2, a1_l3, limit, new_food, new_method, new_note in SPECS:
    c = sym_map[sym]
    matched_idx = []
    for i, it in enumerate(c["items"]):
        if (it.get("a1_l1") == a1_l1
            and it.get("a1_l2", "") == a1_l2
            and it.get("a1_l3", "") == a1_l3
            and it.get("limit_value", "") == limit):
            old_food = it.get("food", "")
            old_method = it.get("method", "")
            old_note = it.get("note", "")
            it["food"] = new_food
            it["method"] = new_method
            it["note"] = new_note
            matched_idx.append(i)
            print(f"[{sym}] idx={i} updated:")
            print(f"  food:  {old_food!r}")
            print(f"     →   {new_food!r}")
            print(f"  method: {old_method!r}")
            print(f"     →   {new_method!r}")
            print(f"  note:   {old_note!r}")
            print(f"     →   {new_note!r}")
            updated_count += 1
    if not matched_idx:
        print(f"WARN: [{sym}] {a1_l1}/{a1_l2}/{a1_l3} limit={limit} NOT FOUND")

print(f"\nTotal updated: {updated_count} rows")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix46-beverage-revert-notes-2026-09-01"
NEW_META = "v82-fix47-grain-l1-l2-pdf-align-2026-09-01"
OLD_TITLE = "[v82-fix46]"
NEW_TITLE = "[v82-fix47]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")