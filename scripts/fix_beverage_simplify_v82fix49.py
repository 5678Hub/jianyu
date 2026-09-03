#!/usr/bin/env python3
"""v82-fix49: 果蔬汁类及其饮料 L2/L3 简化显示（用户肯定方案）

用户确认方案:
1. idx=85 r0005 (0.03 L2 own) 保留 ✓
2. idx=90 r0003 (0.05 含浆果... L2 own) 保留 ✓
3. idx=91 r0004 (0.04 ...葡萄汁) → food 简化为「葡萄汁」, a1_l3 保持 '果蔬汁（浆）'
4. idx=86 (0.5 浓缩果蔬汁（浆）own) → 删除

不动: idx=83 饮料类 L1 own, idx=84 包装饮用水, idx=87 固体饮料, idx=88 含乳饮料
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

# Part 1: 删除 idx=86 (L3 浓缩果蔬汁（浆）own 0.5 row)
removed_idx = []
new_items = []
for i, it in enumerate(items):
    if (it.get("a1_l1") == "饮料类"
        and it.get("a1_l2", "").startswith("果蔬汁类及其饮料")
        and it.get("a1_l3") == "浓缩果蔬汁（浆）"
        and it.get("limit_value") == "0.5"):
        removed_idx.append(i)
        print(f"[DELETE] idx={i} L3 浓缩果蔬汁（浆）own 0.5 row")
        continue
    new_items.append(it)
items[:] = new_items
print(f"Removed idx={removed_idx}")

# Part 2: r0004 food 简化为「葡萄汁」
for it in items:
    if it.get("id") == "r0004":
        old_food = it.get("food", "")
        it["food"] = "葡萄汁"
        print(f"\n[UPDATE] r0004 food: {old_food!r} → '葡萄汁'")
        break

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix48-beverage-l2-own-revert-method-2026-09-01"
NEW_META = "v82-fix49-beverage-simplify-grape-only-2026-09-01"
OLD_TITLE = "[v82-fix48]"
NEW_TITLE = "[v82-fix49]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"\nBumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")