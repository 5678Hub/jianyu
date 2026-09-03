#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix79 完整展开 谷物及其制品(不包括焙烤制品) 树"""
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

tree = data.get("appendix_a1", {}).get("tree", [])

def find_node(nodes, target_name):
    for n in nodes:
        if n.get("name") == target_name:
            return n
        c = find_node(n.get("children", []), target_name)
        if c:
            return c
    return None

# 用全角括号匹配
l1 = find_node(tree, "谷物及其制品(不包括焙烤制品)")
if not l1:
    # 试半角括号
    l1 = find_node(tree, "谷物及其制品（不包括焙烤制品）")
print(f"L1: {l1.get('name') if l1 else 'NOT FOUND'}")

def show(node, depth=0):
    indent = "  " * depth
    print(f"{indent}- {node.get('name')}")
    for c in node.get("children", []):
        show(c, depth + 1)

if l1:
    show(l1)