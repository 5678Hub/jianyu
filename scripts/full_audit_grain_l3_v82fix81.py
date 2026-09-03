#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix81 全量扫描：只统计 L3/L4 节点 own row 数（不算 ancestorsLevels 段）"""
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

GRAIN_L1 = "谷物及其制品(不包括焙烤制品)"

contaminants = data["contaminants"]
tree = data.get("appendix_a1", {}).get("tree", [])

# 谷物章节全部 row
grain_rows_by_tbl = {}
for c in contaminants:
    tbl = c.get("table_no")
    items = c.get("items", [])
    grain_items = []
    for idx, it in enumerate(items):
        if (it.get("a1_l1") == GRAIN_L1
            or it.get("a1_l1") == "谷物及其制品（不包括焙烤制品）"):
            grain_items.append((idx, it))
    if grain_items:
        grain_rows_by_tbl[tbl] = (c.get("contaminant"), c.get("symbol"), grain_items)

def find_l1(nodes, target):
    for n in nodes:
        if n.get("name") == target:
            return n
    return None

grain_root = find_l1(tree, GRAIN_L1) or find_l1(tree, "谷物及其制品（不包括焙烤制品）")

# 收集 L3/L4 节点名
leaf_nodes = []
def collect_leaves(node, path):
    cur_path = path + [node["name"]]
    has_child = bool(node.get("children"))
    if not has_child:
        leaf_nodes.append(cur_path)
    else:
        for c in node.get("children", []):
            collect_leaves(c, cur_path)

# 实际只统计 L3 + L4（不是 L1/L2 own row）
for l2 in grain_root.get("children", []):
    for l3 in l2.get("children", []):
        if not l3.get("children"):  # 叶子 L3
            leaf_nodes.append([GRAIN_L1, l2["name"], l3["name"]])
        else:
            for l4 in l3.get("children", []):
                leaf_nodes.append([GRAIN_L1, l2["name"], l3["name"], l4["name"]])

# 统计每个 L3/L4 节点的 own row
def own_count(path):
    cnt = 0
    for tbl, (contam, symbol, items) in grain_rows_by_tbl.items():
        for idx, it in items:
            a1p_raw = [it.get("a1_l1", ""), it.get("a1_l2", ""),
                       it.get("a1_l3", ""), it.get("a1_l4", "")]
            if a1p_raw[0] in [GRAIN_L1, "谷物及其制品（不包括焙烤制品）"]:
                a1p_raw[0] = GRAIN_L1
            a1p = [x for x in a1p_raw if x]
            if len(a1p) == len(path) and a1p == path:
                cnt += 1
    return cnt

print("=" * 100)
print("【L3/L4 节点 own row 数统计】（仅 own row，不算 ancestorsLevels 段）")
print("=" * 100)

for path in leaf_nodes:
    name = "/".join(path[1:])
    cnt = own_count(path)
    print(f"  L{len(path)-1} {name:55s} | own row: {cnt} 条")