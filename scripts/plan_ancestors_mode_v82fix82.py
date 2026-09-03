#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82 规划：扫描 inlineData 看 L1 通类 row 出现情况 + 规划选项"""
import re, json, sys
from collections import defaultdict
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

# 收集 L1 通类 row（a1_l2='' a1_l3='' a1_l4=''）
l1_generic_rows = []
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        a1l1 = it.get("a1_l1", "")
        a1l2 = it.get("a1_l2", "")
        a1l3 = it.get("a1_l3", "")
        a1l4 = it.get("a1_l4", "")
        if a1l1 and not a1l2 and not a1l3 and not a1l4:
            l1_generic_rows.append({
                "tbl": tbl,
                "contam": contam,
                "symbol": symbol,
                "idx": idx,
                "food": it.get("food", ""),
                "limit": it.get("limit_value", ""),
                "a1l1": a1l1,
            })

# 收集 L2 通类 row（a1_l2 != '' a1_l3='' a1_l4=''）
l2_generic_rows = []
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        a1l1 = it.get("a1_l1", "")
        a1l2 = it.get("a1_l2", "")
        a1l3 = it.get("a1_l3", "")
        a1l4 = it.get("a1_l4", "")
        if a1l1 and a1l2 and not a1l3 and not a1l4:
            l2_generic_rows.append({
                "tbl": tbl,
                "contam": contam,
                "symbol": symbol,
                "idx": idx,
                "food": it.get("food", ""),
                "limit": it.get("limit_value", ""),
                "a1l1": a1l1,
                "a1l2": a1l2,
            })

print("=" * 100)
print("【当前状态扫描】L1 通类 row + L2 通类 row 数量")
print("=" * 100)

print(f"\nL1 通类 row 总数: {len(l1_generic_rows)}")
print("-" * 100)
for r in l1_generic_rows:
    print(f"  表{r['tbl']} {r['contam']}({r['symbol']}) | idx={r['idx']} | {r['limit']} | L1={r['a1l1'][:30]} | food: {r['food'][:50]}")

print(f"\nL2 通类 row 总数: {len(l2_generic_rows)}")
print("-" * 100)
for r in l2_generic_rows:
    print(f"  表{r['tbl']} {r['contam']}({r['symbol']}) | idx={r['idx']} | {r['limit']} | L2={r['a1l2'][:25]} | food: {r['food'][:50]}")

print("\n" + "=" * 100)
print("【规划方案对比】")
print("=" * 100)

print("""
方案 A: ancestorsLevels 全显示（L1+L2 通类都引用）
- 实现: 取消 v82-fix81 的 L1 通类 row 过滤,让 L1/L2 通类 row 都 fall back
- 影响: 有 own row 的 L3 节点(稻谷/玉米/小麦/糙米/大米/小麦粉/玉米粉/麦片/面筋/其他谷物制品)
  会从 L1「谷物及其制品」+ L2「谷物」/「谷物碾磨加工品」/「谷物制品」分层显示
  - 稻谷 ancestorsLevels 段:
    - L1「谷物及其制品」段: idx=63 Pb 0.2(但稻谷在排除项 → 不显示)
    - L2「谷物」段: idx=0 Cd 0.1(稻谷在排除项 → 不显示) + idx=35 总砷(稻谷在排除项 → 不显示) + idx=9 Cr 1.0
  - 大麦 ancestorsLevels 段:
    - L1 段: idx=63 Pb 0.2
    - L2 段: idx=0 Cd 0.1 + idx=35 总砷 0.5 + idx=9 Cr 1.0
  - 麦片 ancestorsLevels 段:
    - L1 段: idx=63 Pb 0.2(麦片在排除项 → 不显示)
    - L2 段: idx=1 Cd 0.1 + idx=36 总砷 0.5 + idx=10 Cr 1.0
- 优点: ancestorsLevels 段显示完整 L1+L2 两层
- 缺点: PDF 原文没专门为「麦片」「面筋」列 row 的 L1 通类 idx=63 也显示(虽然被排除项阻止)

方案 B: ancestorsLevels 只显示 L2 通类（当前 v82-fix81 状态）
- 实现: v82-fix81 过滤 L1 通类 row,只显示 L2 通类 row
- 影响: 有 own row 的 L3 节点 ancestorsLevels 段只显示 L2 通类引用
  - 稻谷 ancestorsLevels 段: L2「谷物」段 Cr 1.0(只有 idx=9,idx=0/35 被稻谷排除项阻止)
  - 大麦 ancestorsLevels 段: L2「谷物」段 Cd 0.1 + 总砷 0.5 + Cr 1.0
  - 麦片 ancestorsLevels 段: L2「谷物碾磨加工品」段 Cd 0.1 + 总砷 0.5 + Cr 1.0
- 优点: 简洁,只显示「直接父级」引用
- 缺点: L1 通类 row 完全不显示(idx=63 Pb 0.2)

方案 C: ancestorsLevels 完全关闭（不显示任何上级分类）
- 实现: 取消 v82-fix81 的 ancestorsLevels for 循环
- 影响: 所有 L3/L4 节点只显示 own row,idx 空节点显示空
- 优点: 严格按 PDF own row 展示,无任何 fallback
- 缺点: idx 空的节点(如大麦/其他谷物/其他谷物碾磨加工品/大米制品/玉米制品/各种面制品等)
  会显示空,无法向上级继承
""")