#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 扫描：所有污染物 row 中与「小麦粉」相关的内容"""
import re, json, sys
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
if not m:
    print("[err] inlineData not found")
    sys.exit(1)

# 括号深度解析 JSON
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
json_str = src[start:end]
data = json.loads(json_str)

contaminants = data.get("contaminants", [])
print(f"总污染物表数: {len(contaminants)}")
print()

wheat_results = []
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, item in enumerate(items):
        food = item.get("food", "")
        a1l1 = item.get("a1_l1", "")
        a1l2 = item.get("a1_l2", "")
        a1l3 = item.get("a1_l3", "")
        a1l4 = item.get("a1_l4", "")
        lv = item.get("limit_value", "")
        # 任何字段包含"小麦"
        if ("小麦" in food or "小麦" in a1l1 or "小麦" in a1l2
            or "小麦" in a1l3 or "小麦" in a1l4):
            wheat_results.append({
                "tbl": tbl,
                "contam": contam,
                "symbol": symbol,
                "idx_in_table": idx,
                "food": food,
                "limit": lv,
                "a1l1": a1l1,
                "a1l2": a1l2,
                "a1l3": a1l3,
                "a1l4": a1l4,
            })

print(f"含「小麦」字段的 row 共 {len(wheat_results)} 条")
print("=" * 100)
for r in wheat_results:
    print(f"[表{r['tbl']} {r['contam']}({r['symbol']})] idx={r['idx_in_table']} 限量={r['limit']}")
    print(f"  food   = {r['food']}")
    print(f"  a1_l1  = {r['a1l1']}")
    print(f"  a1_l2  = {r['a1l2']}")
    print(f"  a1_l3  = {r['a1l3']}")
    print(f"  a1_l4  = {r['a1l4']}")
    print("-" * 100)