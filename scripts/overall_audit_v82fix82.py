#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82 全 13 大类整体扫描：L1 节点 + 全部 row + 全部 L3/L4 节点"""
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
tree = data.get("appendix_a1", {}).get("tree", [])

# 统计每个 L1 节点下的 row 数 + L3/L4 节点数
print("=" * 100)
print("【整体扫描】GB 2762-2025 全 13 大类（A.1 树 L1）核对清单")
print("=" * 100)

def walk_collect_l1(node, target_name, path=()):
    if node.get("name") == target_name:
        return path + (node["name"],), node
    for c in node.get("children", []):
        r = walk_collect_l1(c, target_name, path + (node["name"],))
        if r: return r
    return None

# 收集全部 row
total_rows = 0
for c in contaminants:
    total_rows += len(c.get("items", []))

print(f"\n总污染物表: {len(contaminants)}")
print(f"总 row 数: {total_rows}")

# A.1 树 L1 节点
print(f"\nA.1 树 L1 节点:")
def walk_l1(node, depth=0):
    name = node.get("name", "")
    children_count = len(node.get("children", []))
    grand_count = sum(len(c.get("children", [])) for c in node.get("children", []))
    great_grand = 0
    for c in node.get("children", []):
        for gc in c.get("children", []):
            great_grand += len(gc.get("children", []))
    print(f"  L1 '{name[:40]}' | L2: {children_count} | L3: {grand_count} | L4: {great_grand}")
    for c in node.get("children", []):
        walk_l1(c, depth+1)

for root in tree:
    walk_l1(root, 0)

# 统计每个 L1 节点的 idx 命中 row 数
print("\n" + "=" * 100)
print("【每个 L1 节点的 row 数 + L1 通类 row 数】")
print("=" * 100)

l1_root_nodes = [n.get("name") for n in tree]

# 全 inlineData 收集 L1 通类 row
all_l1_generic = []
for c in contaminants:
    tbl = c.get("table_no")
    for idx, it in enumerate(c.get("items", [])):
        a1l1 = it.get("a1_l1", "")
        if a1l1 and not it.get("a1_l2") and not it.get("a1_l3") and not it.get("a1_l4"):
            all_l1_generic.append((tbl, idx, it))

# 每个 L1 节点的 row 数（任何深度）
for root_name in l1_root_nodes:
    l1_rows = 0
    l1_l3_l4_rows = 0
    for c in contaminants:
        tbl = c.get("table_no")
        contam = c.get("contaminant", "")
        for idx, it in enumerate(c.get("items", [])):
            a1l1 = it.get("a1_l1", "")
            if a1l1 == root_name:
                l1_rows += 1
                if it.get("a1_l3") or it.get("a1_l4"):
                    l1_l3_l4_rows += 1
    print(f"  L1 '{root_name[:40]}' | 总 row: {l1_rows} | L3/L4 own row: {l1_l3_l4_rows}")