#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix79 扫描 A.1 树中「其他谷物制品」L3 children"""
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

def find_node(nodes, target_name):
    for n in nodes:
        if n.get("name") == target_name:
            return n
        c = find_node(n.get("children", []), target_name)
        if c:
            return c
    return None

# 找「谷物及其制品（不包括焙烤制品）」
l1 = find_node(tree, "谷物及其制品（不包括焙烤制品）")
print(f"L1 '谷物及其制品': {l1.get('name') if l1 else 'NOT FOUND'}")
if l1:
    print(f"L1 children:")
    for c in l1.get("children", []):
        print(f"  - {c.get('name')}")
        for cc in c.get("children", []):
            print(f"    - {cc.get('name')}")
            for ccc in cc.get("children", []):
                print(f"      - {ccc.get('name')}")