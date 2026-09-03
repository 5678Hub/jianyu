#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82 v4 对每个 L1 的 idx 空 L3/L4 节点，检查 PDF L2 通类 row 是否能 fall back"""
import re, json
from pathlib import Path
from collections import defaultdict

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

def walk_tree(node, l1_name, path, l3l4_map):
    cur_path = path + (node["name"],)
    if node.get("name") == l1_name:
        for c in node.get("children", []):
            walk_tree(c, l1_name, cur_path, l3l4_map)
        return
    level = len(cur_path) - 2
    if level >= 1:
        l3l4_map[l1_name].append({
            "level": level, "path": cur_path[1:], "name": node["name"],
        })
    for c in node.get("children", []):
        walk_tree(c, l1_name, cur_path, l3l4_map)

l3l4_by_l1 = defaultdict(list)
for root in tree:
    walk_tree(root, root["name"], (), l3l4_by_l1)

# row 按 l1+a1l2 索引
rows_by_l1l2 = defaultdict(list)
for c in contaminants:
    contam = c.get("contaminant", "")
    for idx, it in enumerate(c.get("items", [])):
        a1l1 = it.get("a1_l1", "")
        a1l2 = it.get("a1_l2", "")
        if a1l1:
            rows_by_l1l2[(a1l1, a1l2)].append({"contam": contam, "item": it})

print("=" * 100)
print("【每个 L1 的 idx 空 L3/L4 节点的 L2 通类 row fall back 清单】")
print("=" * 100)

for root_name in [n["name"] for n in tree]:
    row_name = TREE_TO_ROW.get(root_name, root_name)
    l3l4_nodes = l3l4_by_l1.get(root_name, [])
    rows = rows_by_l1l2.get((row_name, ""), [])  # L1 通类 row
    rows_l1_only = rows  # alias

    short = row_name[:22] + ('...' if len(row_name) > 22 else '')

    # 收集 idx 空节点（按 L2 分组）
    idx_empty_by_l2 = defaultdict(list)
    for n in l3l4_nodes:
        has = False
        for c in contaminants:
            for idx, it in enumerate(c.get("items", [])):
                if it.get("a1_l1", "") != row_name: continue
                a1l3 = it.get("a1_l3", "")
                a1l4 = it.get("a1_l4", "")
                if n["level"] == 1 and a1l3 == n["path"][1] and not a1l4:
                    has = True; break
                if n["level"] == 2 and a1l3 == n["path"][1] and a1l4 == n["path"][2]:
                    has = True; break
            if has: break
        if not has:
            l2 = n["path"][0]
            idx_empty_by_l2[l2].append(n)

    if not idx_empty_by_l2 and not rows_l1_only:
        continue

    print(f"\n--- L1 '{short}' ---")
    print(f"  L1 通类 row: {len(rows_l1_only)} 条")
    for r in rows_l1_only:
        print(f"    [L1] {r['contam']} | {r['item'].get('food','')[:30]} | 限量: {r['item'].get('limit','')}")

    for l2, empties in idx_empty_by_l2.items():
        l2_rows = rows_by_l1l2.get((row_name, l2), [])
        print(f"  L2 '{l2[:30]}' 通类 row: {len(l2_rows)} 条")
        for r in l2_rows:
            print(f"    [L2] {r['contam']} | {r['item'].get('food','')[:30]} | 限量: {r['item'].get('limit','')}")
        if not l2_rows:
            print(f"    ⚠️ L2 '{l2}' 没有任何 row，连 L2 通类引用都没有！")
        print(f"  idx 空 L3/L4 节点数: {len(empties)}")