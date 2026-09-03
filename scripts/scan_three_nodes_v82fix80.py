#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix80 扫描三个分类节点的 idx 命中 + ancestorsLevels 推演"""
import re, json, sys
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
i = m.end()
depth = 0; start = i
end_idx = i
while i < len(src):
    if src[i] == '{': depth += 1
    elif src[i] == '}':
        depth -= 1
        if depth == 0:
            end_idx = i + 1
            break
    i += 1
data = json.loads(src[start:end_idx])

contaminants = data["contaminants"]

# 三个分类节点的 pathKey
TARGETS = [
    ("麦片", ["谷物及其制品（不包括焙烤制品）", "谷物碾磨加工品", "麦片"]),
    ("面筋", ["谷物及其制品（不包括焙烤制品）", "谷物制品", "小麦粉制品", "面筋"]),
    ("其他谷物制品", ["谷物及其制品（不包括焙烤制品）", "谷物制品",
                      "其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]"]),
]

print("=" * 100)
print("三个分类节点的污染物限量扫描（own row + ancestorsLevels 推演）")
print("=" * 100)

for tbl_idx, c in enumerate(contaminants):
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    print(f"\n--- 表{tbl} {contam}({symbol}) ---")
    for target_name, target_path in TARGETS:
        own_rows = []
        for it in items:
            a1l1 = it.get("a1_l1", "")
            a1l2 = it.get("a1_l2", "")
            a1l3 = it.get("a1_l3", "")
            a1l4 = it.get("a1_l4", "")
            if (a1l1 == target_path[0]
                and (len(target_path) < 2 or a1l2 == target_path[1])
                and (len(target_path) < 3 or a1l3 == target_path[2])
                and (len(target_path) < 4 or a1l4 == target_path[3])):
                own_rows.append(it)
        if own_rows:
            for it in own_rows:
                lv = it.get("limit_value", "")
                sub = it.get("sub_value", "")
                unit = it.get("unit", "mg/kg")
                food = it.get("food", "")
                main = it.get("main_label", "")
                sub_label = it.get("sub_label", "")
                if sub_label:
                    print(f"  [{target_name}] own: {main}/{sub_label} {sub} {unit} | food={food[:50]}")
                else:
                    print(f"  [{target_name}] own: {lv} {unit} | food={food[:50]}")