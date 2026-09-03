#!/usr/bin/env python3
"""v82-fix55: 6 条长文本 note 规范化（脚注化 / 清空）

用户肯定方案:
- Cd idx=0, Cd idx=1, As idx=35, As idx=36, Cr idx=10: 清空 note → ''
  理由: 「以X计。」整表通用限定,「稻谷除外」「糙米、大米（粉）除外」非脚注是 row 内文(已写在 food 字段)
- Cr idx=9: 改为 'a' (Cr 脚注 a: 稻谷以糙米计。)
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

# 规范化的 6 处
TARGETS = [
    ("Cd", 0,  ""),  # 谷物 0.1 row
    ("Cd", 1,  ""),  # 谷物碾磨加工品 0.1 row
    ("As", 35, ""),  # 谷物 0.5 row
    ("As", 36, ""),  # 谷物碾磨加工品 0.5 row
    ("Cr", 9,  "a"), # 谷物 1.0 row (脚注 a: 稻谷以糙米计。)
    ("Cr", 10, ""),  # 谷物碾磨加工品 1.0 row
]

sym_map = {c.get("symbol"): c for c in data["contaminants"]}
for sym, idx, new_note in TARGETS:
    c = sym_map[sym]
    it = c["items"][idx]
    old_note = it.get("note", "")
    it["note"] = new_note
    food = it.get("food", "")[:40]
    print(f"[{sym}] idx={idx} food={food!r}")
    print(f"  old note: {old_note!r}")
    print(f"  new note: {new_note!r}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix54-grain-l1-note-as-footletter-2026-09-01"
NEW_META = "v82-fix55-batch-normalize-6-notes-2026-09-02"
OLD_TITLE = "[v82-fix54]"
NEW_TITLE = "[v82-fix55]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"\nBumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")