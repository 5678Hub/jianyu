#!/usr/bin/env python3
"""v82-fix54: 把 idx=63 row 的 note 字段改为脚注字母 'a' (PDF 标准做法)

用户反馈：「备注, 我不需要这样的备注。你看看其他的食品分类中的脚注是怎么做的,按照同样的思路去做」

PDF 表 1 脚注定义 (data/gb2762/_meta/GB2762-2025.md L536):
  a 稻谷以糙米计

idx=63 当前 note='以Pb计。稻谷以糙米计。麦片、面筋、粥类罐头、带馅(料)面米制品除外。'
  - '以Pb计。' → 整表通用限定,不应在 note
  - '稻谷以糙米计。' → PDF 脚注 a 的内容,应改为字母 'a'
  - '麦片、面筋、粥类罐头、带馅(料)面米制品除外。' → 已写在 food 字段 '〔...除外〕',重复

修复:
  - idx=63 note 改为 'a' (单一字母,渲染时显示 fn-mark badge 'a',鼠标悬停显示脚注 a 完整内容)
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

for i, it in enumerate(pb["items"]):
    if (it.get("a1_l1", "") == "谷物及其制品（不包括焙烤制品）"
        and it.get("a1_l2", "") == ""
        and it.get("a1_l3", "") == ""
        and it.get("limit_value", "") == "0.2"):
        old_note = it.get("note", "")
        it["note"] = "a"
        print(f"[UPDATE] idx={i} (谷物 L1 own 0.2 row):")
        print(f"  old note: {old_note!r}")
        print(f"  new note: 'a' (PDF 脚注 a: 稻谷以糙米计。)")
        break

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix53-restore-l2-juice-0-03-2026-09-01"
NEW_META = "v82-fix54-grain-l1-note-as-footletter-2026-09-01"
OLD_TITLE = "[v82-fix53]"
NEW_TITLE = "[v82-fix54]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")