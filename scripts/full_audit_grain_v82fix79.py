#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix79 全量扫描「谷物及其制品(不包括焙烤制品)」大类全部 row + 推断每个节点的 PDF 表达"""
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

# 1) 列出当前 inlineData 谷物章节全部 row（按表分组）
contaminants = data["contaminants"]

print("=" * 100)
print(f"【现状扫描】{GRAIN_L1} 大类全部 row（按污染物表分组）")
print("=" * 100)

grain_rows_by_tbl = {}  # tbl -> list of (idx, item)
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    grain_items = []
    for idx, it in enumerate(items):
        if (it.get("a1_l1") == GRAIN_L1
            or it.get("a1_l1") == "谷物及其制品（不包括焙烤制品）"):
            grain_items.append((idx, it))
    if grain_items:
        grain_rows_by_tbl[tbl] = (contam, symbol, grain_items)

for tbl, (contam, symbol, items) in grain_rows_by_tbl.items():
    print(f"\n--- 表{tbl} {contam}({symbol}) {len(items)} 条 ---")
    for idx, it in items:
        a1l2 = it.get("a1_l2", "")
        a1l3 = it.get("a1_l3", "")
        a1l4 = it.get("a1_l4", "")
        lv = it.get("limit_value", "")
        sub = it.get("sub_value", "")
        sub_label = it.get("sub_label", "")
        main_label = it.get("main_label", "")
        food = it.get("food", "")[:40]
        path_repr = "/".join(filter(None, [a1l2, a1l3, a1l4]))
        if sub_label:
            print(f"  [pos={idx}] {path_repr:35s} | {main_label}/{sub_label}={sub} | food={food}")
        else:
            print(f"  [pos={idx}] {path_repr:35s} | {lv} | food={food}")

# 2) 列 A.1 树中谷物章节全部 L3/L4 节点
tree = data.get("appendix_a1", {}).get("tree", [])

def find_l1(nodes, target):
    for n in nodes:
        if n.get("name") == target:
            return n
    return None

grain_root = find_l1(tree, GRAIN_L1)
if grain_root is None:
    grain_root = find_l1(tree, "谷物及其制品（不包括焙烤制品）")

if grain_root is None:
    print("\n[!] 树中找不到「谷物及其制品(不包括焙烤制品)」L1 节点")
    sys.exit(1)

print("\n" + "=" * 100)
print(f"【A.1 树结构】{GRAIN_L1} 大类全部节点（用于对照 PDF 表达覆盖）")
print("=" * 100)

def walk(node, depth=0):
    name = node.get("name", "")
    print(f"{'  ' * depth}└─ {name}")
    for child in node.get("children", []):
        walk(child, depth + 1)

walk(grain_root)

# 3) 对比：每个 L3/L4 节点实际显示的 own row 数量
print("\n" + "=" * 100)
print("【对比】每个 L3/L4 节点当前 idx 命中 own row 数（含 idx=0 通类）")
print("=" * 100)

# 收集所有节点的 idx 命中 (模拟 idx Map)
def collect_idx_hit(nodes, path):
    hits = {}
    for n in nodes:
        cur_path = path + [n["name"]]
        key = "|".join(cur_path)
        # 该节点直接挂的 row（a1 路径完全匹配 cur_path）
        direct = []
        for tbl, (contam, symbol, items) in grain_rows_by_tbl.items():
            for idx, it in items:
                a1p = [it.get("a1_l1", ""), it.get("a1_l2", ""),
                       it.get("a1_l3", ""), it.get("a1_l4", "")]
                # 标准化 L1
                if a1p[0] in [GRAIN_L1, "谷物及其制品（不包括焙烤制品）"]:
                    a1p[0] = GRAIN_L1
                if a1p[:len(cur_path)] == cur_path:
                    direct.append((tbl, contam, symbol, idx, it))
        if direct:
            hits[key] = direct
        if n.get("children"):
            hits.update(collect_idx_hit(n["children"], cur_path))
    return hits

hits = collect_idx_hit(grain_root.get("children", []), [GRAIN_L1])

for key, rows in hits.items():
    parts = key.split("|")
    # 简化显示
    name = "/".join(parts[1:]) if len(parts) > 1 else parts[0]
    contaminants_summary = []
    for tbl, contam, symbol, idx, it in rows:
        lv = it.get("limit_value", "")
        sub = it.get("sub_value", "")
        sub_label = it.get("sub_label", "")
        main_label = it.get("main_label", "")
        if sub_label and sub != "—":
            contaminants_summary.append(f"{main_label}/{sub_label}={sub}")
        elif lv and lv != "—":
            contaminants_summary.append(f"{lv}")
    print(f"  {name:45s} | {' '.join(contaminants_summary)}")

# 4) PDF 表达差异点（v82-fix57-80 后的认知）
print("\n" + "=" * 100)
print("【推断差异点】（基于 v82-fix75-80 后的 PDF 严格展示规则）")
print("=" * 100)
print("""
1. idx=68 主 row v82-fix80 挂「麦片」L3（a1_l3='麦片'），但 v82-fix80 实施时：
   - 之前 v82-fix77 改成 a1_l3='其他谷物制品'，导致「谷物制品」L2 own row = 1 条
   - v82-fix78 ancestorsLevels 显示 L1 通类 idx=63，「谷物制品」L2 显示 1 条
   - v82-fix80 改回 a1_l3='麦片'，现在「谷物制品」L2 idx 空

2. idx=68 v82-fix77 之前 a1_l3='其他谷物制品'（不带 [例如：带馅（料）面米制品、粥类罐头等]），
   v82-fix80 复制挂 a1_l3='其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]'。
   「其他谷物制品」与「其他谷物制品[...]」是否同一节点待确认（树中只有后者）。

3. 谷物碾磨加工品 L2 下 idx=68 复制后的注册逻辑未人工测试。

4. 表 2 Cd 谷物章节 idx=2-4（v82-fix73 加的复制）是否画蛇添足未核 PDF 原文。
""")