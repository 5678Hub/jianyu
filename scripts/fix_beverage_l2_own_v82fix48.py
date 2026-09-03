#!/usr/bin/env python3
"""v82-fix48: 果蔬汁类及其饮料 L2 own row 修复 + 撤回 v82-fix47 冗余 method 字段

两件事:
1. 撤回 v82-fix47 添加的 method 字段（前端只读 inspection_method，method 是冗余字段）
2. 恢复 L2 果蔬汁类及其饮料 own row（v82-fix46 删除的 idx=85 0.03 row）

PDF 表 1 L2 果蔬汁类及其饮料 spec:
  food = 果蔬汁类及其饮料〔含浆果及小粒水果的果蔬汁类及其饮料、浓缩果蔬汁(浆)除外〕
  limit = 0.03
  inspection_method = GB 5009.12 (与 idx=84 包装饮用水一致——简短形式)
  note = '' (按用户「附录没有就不写」原则)

副作用告知：0.03 row 会通过 walkExact Fallback B 也注册到 L3 浓缩果蔬汁（浆）下，
  与 L3 own row 0.5 共存显示。如不希望需改 walkExact Fallback B 逻辑。
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

# === Part 1: 撤回 v82-fix47 添加的 method 字段（仅谷物 L1/L2 own rows）===
# 之前 v82-fix47 错误地用 method 字段而非 inspection_method 字段,前端不读 method
# 需要清空 method 字段(不影响 inspection_method 原值)
GRAIN_L1L2_PAIRS = [
    ("Pb", "谷物及其制品（不包括焙烤制品）", "", ""),         # Pb idx=63
    ("Cd", "谷物及其制品（不包括焙烤制品）", "谷物", ""),       # Cd idx=0
    ("Cd", "谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", ""), # Cd idx=1
    ("As", "谷物及其制品（不包括焙烤制品）", "谷物", ""),       # As idx=35
    ("As", "谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", ""), # As idx=36
    ("Cr", "谷物及其制品（不包括焙烤制品）", "谷物", ""),       # Cr idx=9
    ("Cr", "谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", ""), # Cr idx=10
]

sym_map = {c.get("symbol"): c for c in data["contaminants"]}
cleared_method = 0
for sym, a1_l1, a1_l2, _a1_l3 in GRAIN_L1L2_PAIRS:
    c = sym_map[sym]
    for it in c["items"]:
        if (it.get("a1_l1") == a1_l1
            and it.get("a1_l2", "") == a1_l2
            and it.get("a1_l3", "") == ""
            and "method" in it):
            old_method = it["method"]
            del it["method"]
            cleared_method += 1
            print(f"[{sym}] {a1_l1[:20]}/{a1_l2[:15]} cleared method: {old_method!r}")

print(f"\nCleared {cleared_method} redundant method fields")

# === Part 2: 恢复 L2 果蔬汁类及其饮料 own row (0.03) ===
pb = sym_map["Pb"]
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
# 插入到合适位置: idx=84 (L2 包装饮用水) 之后
# 当前顺序: idx=83 L1饮料类own / idx=84 L2包装饮用水 / idx=85 L3浓缩果蔬汁（浆）
# 插入到 idx=85 之前（即包装饮水之后, 浓缩果蔬汁之前）
insert_pos = None
for i, it in enumerate(pb["items"]):
    if (it.get("a1_l1") == "饮料类"
        and it.get("a1_l2") == "包装饮用水"
        and it.get("a1_l3") == ""):
        insert_pos = i + 1
        break
if insert_pos is None:
    print("WARN: anchor L2 包装饮用水 not found, appending at end")
    pb["items"].append(new_row)
else:
    pb["items"].insert(insert_pos, new_row)
    print(f"\nInserted new row at pos {insert_pos}: r0005 L2 果蔬汁类及其饮料 own row 0.03")
    print(f"  food = {new_row['food']}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix47-grain-l1-l2-pdf-align-2026-09-01"
NEW_META = "v82-fix48-beverage-l2-own-revert-method-2026-09-01"
OLD_TITLE = "[v82-fix47]"
NEW_TITLE = "[v82-fix48]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")