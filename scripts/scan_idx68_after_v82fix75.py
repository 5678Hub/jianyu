#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 检查 idx=68 当前实际位置和字段"""
import re, json, sys
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
i = m.end()
depth = 0; start = i
while i < len(src):
    if src[i] == '{': depth += 1
    elif src[i] == '}':
        depth -= 1
        if depth == 0: break
    i += 1
end = i + 1
data = json.loads(src[start:end])

for c in data["contaminants"]:
    if c.get("table_no") == 1:
        items = c["items"]
        print(f"Pb 表共 {len(items)} 条 row")
        # 找 food='麦片、面筋、粥类罐头、带馅(料)面米制品' 的 row
        for i, it in enumerate(items):
            if "麦片" in it.get("food","") and "面筋" in it.get("food",""):
                print(f"  [position={i}]")
                for k in ['food', 'a1_l1', 'a1_l2', 'a1_l3', 'a1_l4', 'limit_value']:
                    print(f"    {k}: {it.get(k, '')}")
        break