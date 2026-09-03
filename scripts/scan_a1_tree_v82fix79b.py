#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix79 扫描 A.1 树 全文"""
import re, json
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

# 找 A.1 树
tree = data.get("appendix_a1", {}).get("tree", [])
print(f"树根数量: {len(tree)}")
print("=== L1 全部节点 ===")
for n in tree:
    print(f"  - {n.get('name')}")