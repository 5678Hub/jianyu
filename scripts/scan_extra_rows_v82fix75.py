#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 扫描：谷物章节 L3 own row 详细列表（疑似画蛇添足）"""
import re, json, sys
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
if not m:
    print("[err] inlineData not found")
    sys.exit(1)

i = m.end()
depth = 0
start = i
while i < len(src):
    ch = src[i]
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            break
    i += 1

end = i + 1
data = json.loads(src[start:end])

contaminants = data.get("contaminants", [])

print("【谷物章节 L3 own row 全部明细】")
print("=" * 100)
print(f"{'表':<4} {'污染物':<8} {'idx':<4} {'L3节点':<20} {'限量':<8} {'food（前40字）':<40}")
print("-" * 100)

for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        a1l1 = it.get("a1_l1", "")
        a1l3 = it.get("a1_l3", "")
        if "谷物" in a1l1 and a1l3:
            lv = it.get("limit_value", "")
            food = it.get("food", "")[:40]
            print(f"{tbl:<4} {contam}({symbol}){'':<3} {idx:<4} {a1l3:<20} {lv:<8} {food:<40}")
print("=" * 100)