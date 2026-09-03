#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 扫描：谷物章节 L1 下所有 own row（a1_l3 != ''）"""
import re, json, sys
from pathlib import Path
from collections import defaultdict

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
json_str = src[start:end]
data = json.loads(json_str)

contaminants = data.get("contaminants", [])

# 谷物章节：a1_l1 == '谷物及其制品（不包括焙烤制品）'
print("=" * 100)
print("【谷物及其制品（不包括焙烤制品）】L1 下所有污染物 own row 统计")
print("=" * 100)

for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    # 只看 a1_l3 != '' 的 own row + a1_l2 != '' 但 a1_l3 == '' 的 L2 own row
    own_l3 = [it for it in items if it.get("a1_l3")]
    own_l2 = [it for it in items if it.get("a1_l2") and not it.get("a1_l3")]
    own_l1 = [it for it in items if it.get("a1_l1") and not it.get("a1_l2")]
    own_grain_l3 = [it for it in own_l3 if "谷物" in it.get("a1_l1", "")]
    own_grain_l2 = [it for it in own_l2 if "谷物" in it.get("a1_l1", "")]

    if own_grain_l3 or own_grain_l2 or any("谷物" in it.get("a1_l1","") for it in own_l1):
        print(f"\n--- 表{tbl} {contam}({symbol}) ---")
        if own_grain_l3:
            print(f"  L3 own row 数量: {len(own_grain_l3)}")
            for it in own_grain_l3:
                print(f"    [idx={items.index(it)}] {it.get('a1_l3')[:30]:30s} | {it.get('limit_value')} | food={it.get('food')[:50]}")
        if own_grain_l2:
            print(f"  L2 own row 数量: {len(own_grain_l2)}")
            for it in own_grain_l2:
                print(f"    [idx={items.index(it)}] {it.get('a1_l2')[:30]:30s} | {it.get('limit_value')} | food={it.get('food')[:50]}")
        # L1 通类
        own_grain_l1 = [it for it in own_l1 if "谷物" in it.get("a1_l1","")]
        if own_grain_l1:
            print(f"  L1 通类 row 数量: {len(own_grain_l1)}")
            for it in own_grain_l1:
                print(f"    [idx={items.index(it)}] food={it.get('food')[:60]} | {it.get('limit_value')}")