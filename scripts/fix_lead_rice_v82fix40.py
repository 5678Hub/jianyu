#!/usr/bin/env python3
"""v82-fix40: 修正 4 条铅 row 0.5→0.2（糙米、大米、小麦粉、玉米粉、玉米糁等）

v82-fix36 时把 L2 谷物碾磨加工品本级的铅 0.5 row 克隆到 4 个 L3 节点。
但对照 PDF 表 1，糙米/大米(粉)/小麦粉/玉米粉/玉米糁等属于
「谷物及其制品*〔麦片、面筋、粥类罐头、带馅(料)面米制品除外〕」，
正确限量是 0.2，不是 0.5。

0.5 仅适用于麦片、面筋、粥类罐头、带馅(料)面米制品。
"""
import json
import sys
from pathlib import Path

FILE = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")

# 解析 inlineData
html = FILE.read_text(encoding="utf-8")
start_tag = '<script type="application/json" id="inlineData">'
end_tag = '</script>'
start = html.index(start_tag) + len(start_tag)
# 括号深度跟踪找 JSON 结束
BACKSLASH = chr(92); QUOTE = '"'
depth = 0; in_str = False; esc = False; obj_end = -1
for offset_ch in range(start, len(html)):
    ch = html[offset_ch]
    if in_str:
        if esc: False
        elif ch == BACKSLASH: esc = True
        elif ch == QUOTE: in_str = False
        continue
    if ch == QUOTE: in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = offset_ch + 1; break
if obj_end == -1:
    sys.exit("ERROR: inlineData JSON not found")

raw_json = html[start:obj_end]
data = json.loads(raw_json)

# 找污染物「铅」块
lead = next((c for c in data["contaminants"] if c.get("symbol") == "Pb"), None)
if lead is None:
    sys.exit("ERROR: lead contaminant block not found")

items = lead["items"]
target_food = "糙米、大米、小麦粉、玉米粉、玉米糁等"
fixed_indices = []
for i, item in enumerate(items):
    if item.get("food") == target_food and item.get("limit_value") == "0.5":
        items[i]["limit_value"] = "0.2"
        fixed_indices.append(i)

print(f"Fixed {len(fixed_indices)} rows: indices {fixed_indices}")

# 写回（保留 unicode 中文，compact 格式与原文件一致）
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_VER = "v82-fix38-hg-l2-empty-fix-2026-09-01"
NEW_VER = "v82-fix40-lead-rice-05-to-02-2026-09-01"
count = new_html.count(OLD_VER)
new_html = new_html.replace(OLD_VER, NEW_VER)
print(f"Bumped version {count} places: {OLD_VER} → {NEW_VER}")

FILE.write_text(new_html, encoding="utf-8")
print("OK")