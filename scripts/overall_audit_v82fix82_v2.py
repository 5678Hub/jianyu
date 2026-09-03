#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82 v2 全 13 大类整体扫描：修正 tree L1 与 row a1_l1 括号不一致问题"""
import re, json, sys
from pathlib import Path

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

# tree L1 name → row a1_l1 name 归一映射（半角括号 vs 全角括号）
TREE_TO_ROW = {
    '谷物及其制品(不包括焙烤制品)': '谷物及其制品（不包括焙烤制品）',
}

print("=" * 100)
print("【整体扫描 v2】修正括号问题后，全 L1 节点 row 数 + L3/L4 own row 数 + idx 空节点列表")
print("=" * 100)

total_rows = 0
for c in contaminants:
    total_rows += len(c.get("items", []))
print(f"\n总污染物表: {len(contaminants)}, 总 row 数: {total_rows}")

# 全部 row 的 a1_l1 计数
from collections import Counter
a1l1_count = Counter()
for c in contaminants:
    for it in c.get("items", []):
        a1l1_count[it.get("a1_l1", "")] += 1

# tree L1 列表
l1_names_tree = [n.get("name", "") for n in tree]
print(f"\nA.1 tree L1 节点数: {len(l1_names_tree)}")

print("\n" + "=" * 100)
print("每个 L1 节点的 row 数 + L3/L4 own row 数 + idx 空 L3/L4 节点数")
print("=" * 100)

for root_name in l1_names_tree:
    row_name = TREE_TO_ROW.get(root_name, root_name)

    # 该 L1 下全部 row（按 a1_l1 匹配）
    l1_rows_total = 0
    l3_l4_own_rows = 0
    by_contam = {}  # contam -> [(idx, a1l1, a1l2, a1l3, a1l4, food)]
    for c in contaminants:
        contam_name = c.get("contaminant", "")
        for idx, it in enumerate(c.get("items", [])):
            if it.get("a1_l1", "") == row_name:
                l1_rows_total += 1
                if it.get("a1_l3") or it.get("a1_l4"):
                    l3_l4_own_rows += 1
                by_contam.setdefault(contam_name, []).append((idx, it))

    # L3/L4 节点列表（tree 展开）
    def collect_l3l4(node, path):
        if node.get("name") == root_name:
            # 展开这个 L1 的所有 L3/L4 节点
            result = []
            def walk(n, p):
                if n.get("name") == root_name:
                    for c2 in n.get("children", []):
                        walk(c2, p + (c2["name"],))
                else:
                    # n 是 L2/L3/L4 节点
                    result.append((p, n.get("name", ""), n.get("children", [])))
                    for c2 in n.get("children", []):
                        walk(c2, p + (n["name"],))
            walk(n, ())
            return result
        for c in node.get("children", []):
            r = collect_l3l4(c, path + (node["name"],))
            if r: return r
        return None

    l3_l4_nodes = collect_l3l4(tree[0], ())
    if not l3_l4_nodes:
        # 单独从 root 找
        for root_node in tree:
            if root_node.get("name") == root_name:
                l3_l4_nodes = []
                def walk2(n, p):
                    if n.get("name") == root_name:
                        for c2 in n.get("children", []):
                            walk2(c2, p + (c2["name"],))
                    else:
                        l3_l4_nodes.append((p, n.get("name", ""), n.get("children", [])))
                        for c2 in n.get("children", []):
                            walk2(c2, p + (n["name"],))
                walk2(root_node, ())
                break

    # idx 空 L3/L4 节点 = 该 L1 下所有 L3/L4 节点中，没有任何 L3/L4 own row 挂载的
    idx_empty_l3l4 = []
    for path, node_name, grandchildren in l3_l4_nodes:
        # path 是父级链，例如 ('L1', 'L2', 'L3') or ('L1', 'L2', 'L3', 'L4')
        # 节点自身的层级（path 长度）：
        # path 长 1 = L2 节点（"谷物制品"）
        # path 长 2 = L3 节点（"小麦粉"）
        # path 长 3 = L4 节点（"面筋"）
        if len(path) >= 2:  # L3 or L4
            # 检查该节点下是否有 row 挂载
            node_has_row = False
            for c in contaminants:
                for idx, it in enumerate(c.get("items", [])):
                    if it.get("a1_l1", "") == row_name:
                        # 节点匹配：判断 path 是不是 (a1_l2, a1_l3, [a1_l4])
                        a1l2 = it.get("a1_l2", "")
                        a1l3 = it.get("a1_l3", "")
                        a1l4 = it.get("a1_l4", "")
                        # path[0] = L2 节点名, path[1] = L3, path[2] = L4
                        if len(path) == 2 and it.get("a1_l3") == path[1] and not it.get("a1_l4"):
                            node_has_row = True; break
                        elif len(path) == 3 and it.get("a1_l3") == path[1] and it.get("a1_l4") == path[2]:
                            node_has_row = True; break
                if node_has_row: break
            if not node_has_row:
                idx_empty_l3l4.append((path, node_name))

    short = row_name[:24]
    print(f"\n  L1 '{short}{'...' if len(row_name)>24 else ''}'")
    print(f"    总 row: {l1_rows_total} | L3/L4 own row: {l3_l4_own_rows}")
    if idx_empty_l3l4:
        print(f"    idx 空 L3/L4 节点数: {len(idx_empty_l3l4)}")
        for path, name in idx_empty_l3l4:
            print(f"      - {' > '.join(path[1:])} ({name})")
    else:
        print(f"    idx 空 L3/L4 节点: 无")

print("\n" + "=" * 100)
print("汇总: a1_l1 row 计数")
print("=" * 100)
for k, v in sorted(a1l1_count.items(), key=lambda x: -x[1]):
    print(f"  {repr(k):60s} {v}")