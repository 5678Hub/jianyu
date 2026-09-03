#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82 v3 全 L1 扫描：修复 tree 遍历"""
import re, json
from pathlib import Path
from collections import defaultdict, Counter

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
i = m.end(); depth = 0; start = i; end_idx = i
while i < len(src):
    if src[i] == '{': depth += 1
    elif src[i] == '}':
        depth -= 1
        if depth == 0: end_idx = i + 1; break
    i += 1
data = json.loads(src[start:end_idx])

contaminants = data["contaminants"]
tree = data.get("appendix_a1", {}).get("tree", [])

TREE_TO_ROW = {
    '谷物及其制品(不包括焙烤制品)': '谷物及其制品（不包括焙烤制品）',
}

# 1. 把 tree 整理成 l1_root → {l3_nodes, l4_nodes}
def walk_tree(node, l1_name, path, l3l4_map):
    cur_path = path + (node["name"],)
    if node.get("name") == l1_name:
        # 进入 L1，展开下层
        for c in node.get("children", []):
            walk_tree(c, l1_name, cur_path, l3l4_map)
        return
    # 否则 node 是 L2/L3/L4
    level = len(cur_path) - 2  # L2=0, L3=1, L4=2
    if level >= 1:  # L3 或 L4
        l3l4_map[l1_name].append({
            "level": level,  # 1=L3, 2=L4
            "path": cur_path[1:],  # (L2, L3[, L4])
            "name": node["name"],
        })
    for c in node.get("children", []):
        walk_tree(c, l1_name, cur_path, l3l4_map)

l3l4_by_l1 = defaultdict(list)
for root in tree:
    l1 = root["name"]
    walk_tree(root, l1, (), l3l4_by_l1)

# 2. 按 a1_l1（row 名）分桶 row
row_by_l1 = defaultdict(list)  # row_name (fullwidth) → list of row dict
for c in contaminants:
    for idx, it in enumerate(c.get("items", [])):
        a1l1 = it.get("a1_l1", "")
        if a1l1:
            row_by_l1[a1l1].append(it)

# 3. 输出每个 L1 的核对清单
print("=" * 100)
print("【整体扫描 v3】修正括号 + tree 遍历修复后，全 L1 节点核对清单")
print("=" * 100)

for root_name in [n["name"] for n in tree]:
    row_name = TREE_TO_ROW.get(root_name, root_name)
    l3l4_nodes = l3l4_by_l1.get(root_name, [])

    rows = row_by_l1.get(row_name, [])
    l1_rows = len(rows)
    l3l4_own = sum(1 for r in rows if r.get("a1_l3") or r.get("a1_l4"))

    # idx 空节点（该 L1 下 L3/L4 节点，没有任何 row 挂载）
    idx_empty = []
    for n in l3l4_nodes:
        has = False
        for r in rows:
            a1l2 = r.get("a1_l2", "")
            a1l3 = r.get("a1_l3", "")
            a1l4 = r.get("a1_l4", "")
            if n["level"] == 1 and a1l3 == n["path"][1] and not a1l4:
                has = True; break
            if n["level"] == 2 and a1l3 == n["path"][1] and a1l4 == n["path"][2]:
                has = True; break
        if not has:
            idx_empty.append(n)

    short = row_name[:22] + ('...' if len(row_name) > 22 else '')
    print(f"\n  L1 '{short}'")
    print(f"    总 row: {l1_rows} | L3/L4 own row: {l3l4_own} | L3/L4 节点数: {len(l3l4_nodes)} | idx 空 L3/L4: {len(idx_empty)}")
    if idx_empty:
        for n in idx_empty:
            tag = "L3" if n["level"] == 1 else "L4"
            print(f"      {tag} 空: {' / '.join(n['path'])}")