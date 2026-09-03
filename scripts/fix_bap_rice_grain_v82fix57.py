#!/usr/bin/env python3
"""v82-fix57: BaP idx=6 (L3 稻谷) food 改为 PDF 完整原文 + note='a'

用户肯定方案:
- food: '稻谷' → '稻谷a、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)'
- note: '' → 'a' (PDF脚注 a: 稻谷以糙米计。)
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

bap = next(c for c in data["contaminants"] if c.get("symbol") == "BaP")
for i, it in enumerate(bap["items"]):
    if (it.get("a1_l1") == "谷物及其制品（不包括焙烤制品）"
        and it.get("a1_l2", "") == "谷物"
        and it.get("a1_l3") == "稻谷"):
        old_food = it.get("food", "")
        old_note = it.get("note", "")
        it["food"] = "稻谷a、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)"
        it["note"] = "a"
        print(f"[UPDATE] idx={i} (BaP L3 稻谷)")
        print(f"  food: {old_food!r} → {it['food']!r}")
        print(f"  note: {old_note!r} → 'a'")
        break

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix56-delete-idx68-grain-l1-0-5-2026-09-02"
NEW_META = "v82-fix57-bap-rice-grain-full-pdf-text-2026-09-02"
OLD_TITLE = "[v82-fix56]"
NEW_TITLE = "[v82-fix57]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")