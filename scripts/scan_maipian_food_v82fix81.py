#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix81 扫描「麦片」在 inlineData 全部 row food 字段中出现情况"""
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

print("【麦片】在 inlineData 全部 row food 字段中出现情况")
print("=" * 100)

for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        food = it.get("food", "")
        if "麦片" in food:
            lv = it.get("limit_value", "")
            sub = it.get("sub_value", "")
            sub_label = it.get("sub_label", "")
            main_label = it.get("main_label", "")
            a1l2 = it.get("a1_l2", "")
            a1l3 = it.get("a1_l3", "")
            a1l4 = it.get("a1_l4", "")
            a1_repr = "/".join(filter(None, [a1l2, a1l3, a1l4]))
            if sub_label and sub != "—":
                value_repr = f"{main_label}/{sub_label}={sub}"
            elif lv:
                value_repr = lv
            else:
                value_repr = "—"
            print(f"  表{tbl} {contam}({symbol}) | {value_repr:25s} | a1:{a1_repr:40s} | food: {food}")