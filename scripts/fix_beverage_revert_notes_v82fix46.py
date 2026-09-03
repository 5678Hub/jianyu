#!/usr/bin/env python3
"""v82-fix46: 撤销 v82-fix44 的未授权改动 + 删除 idx=85 0.03 row

用户反馈：
1. 备注是不是你新增的——撤回所有备注改动（idx=85/r0003/r0004 的 note 字段清空）
2. 浓缩果蔬汁（浆）下的 0.03 row 不该出现——idx=85 删除
   （注：idx=85 原本是 L2 果蔬汁类及其饮料本级 row，walkExact Fallback 让它也出现在
   L3 浓缩果蔬汁（浆） 下。删除后 L2 本级只剩 0.05 row。如需保留 L2 0.03 row 但不显示在 L3，需改 walkExact）
3. 方法字段（method）按用户原 spec 保留（不要乱动）
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

lead = next((c for c in data["contaminants"] if c.get("symbol") == "Pb"), None)
if lead is None:
    sys.exit("ERROR: lead contaminant block not found")

items = lead["items"]

# 1) 删 idx=85 (L2 果蔬汁类及其饮料 0.03 row)
removed = []
new_items = []
for i, it in enumerate(items):
    if (it.get("a1_l1") == "饮料类"
        and it.get("a1_l2", "").startswith("果蔬汁类及其饮料")
        and it.get("a1_l3") == "" and it.get("limit_value") == "0.03"):
        removed.append(i)
        continue
    new_items.append(it)
items[:] = new_items
print(f"Removed Pb idx={removed} (L2 果蔬汁类及其饮料 0.03 row)")

# 2) 清空 r0003 / r0004 的 note（v82-fix44 我加的备注）
for i, it in enumerate(items):
    if it.get("id") in ("r0003", "r0004"):
        old_note = it.get("note", "")
        it["note"] = ""
        print(f"Cleared note for {it['id']}: {old_note!r} → ''")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix45-nut-cooked-food-fix-2026-09-01"
NEW_META = "v82-fix46-beverage-revert-notes-2026-09-01"
OLD_TITLE = "[v82-fix45]"
NEW_TITLE = "[v82-fix46]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")