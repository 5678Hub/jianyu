#!/usr/bin/env python3
"""v82-fix58: Cd idx=3/4 简略化（与 Hg/BaP 入口合并+其他简略风格一致）

用户反馈: 「使用这样的格式」（合并表达入口 + 其他 L3 row 各自简略）
- Cd idx=2 food 保持 '稻谷、糙米、大米(粉)' (合并表达入口, 已确认)
- Cd idx=3 food 改为 '糙米' (简略)
- Cd idx=4 food 改为 '大米(粉)' (简略)
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

cd = next(c for c in data["contaminants"] if c.get("symbol") == "Cd")
TARGETS = [
    (3, "糙米（包括色稻米）", "糙米"),
    (4, "大米（粉）", "大米(粉)"),
]
for idx, a1_l3, new_food in TARGETS:
    it = cd["items"][idx]
    if it.get("a1_l3") != a1_l3:
        print(f"WARN: idx={idx} a1_l3 != {a1_l3!r}, skip")
        continue
    old_food = it.get("food", "")
    it["food"] = new_food
    print(f"[UPDATE] idx={idx} (Cd L3 {a1_l3})")
    print(f"  food: {old_food!r} → {new_food!r}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix57-bap-rice-grain-full-pdf-text-2026-09-02"
NEW_META = "v82-fix58-cd-idx3-4-simplify-food-2026-09-02"
OLD_TITLE = "[v82-fix57]"
NEW_TITLE = "[v82-fix58]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")