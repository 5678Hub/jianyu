#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 扫描：表4 砷 谷物章节全部 row 完整字段"""
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

# 找表 4 砷
for c in contaminants:
    if c.get("table_no") == 4:
        items = c.get("items", [])
        print(f"表4 污染物: {c.get('contaminant')}({c.get('symbol')})")
        print(f"污染物定义: contaminant_def={c.get('contaminant_def', '')}")
        print()
        for idx, it in enumerate(items):
            a1l1 = it.get("a1_l1", "")
            a1l3 = it.get("a1_l3", "")
            if "谷物" in a1l1 or a1l3 or "稻谷" in it.get("food","") or "大米" in it.get("food","") or "糙米" in it.get("food",""):
                print(f"  [idx={idx}]")
                for k, v in it.items():
                    print(f"    {k}: {v}")
                print()
        break