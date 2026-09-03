#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix81 扫描「大麦」节点的 idx 命中 + ancestorsLevels 推演"""
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
DAMAI_PATH = [GRAIN_L1, "谷物", "大麦（包括青稞）"]

contaminants = data["contaminants"]

print("=" * 100)
print(f"【大麦（包括青稞）】L3 节点 idx 命中 + 推断")
print("=" * 100)

# 1) 大麦 own row
print(f"\n本级 own row:")
own_cnt = 0
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        a1p_raw = [it.get("a1_l1", ""), it.get("a1_l2", ""),
                   it.get("a1_l3", ""), it.get("a1_l4", "")]
        if a1p_raw[0] in [GRAIN_L1, "谷物及其制品（不包括焙烤制品）"]:
            a1p_raw[0] = GRAIN_L1
        a1p = [x for x in a1p_raw if x]
        if len(a1p) == len(DAMAI_PATH) and a1p == DAMAI_PATH:
            own_cnt += 1
            lv = it.get("limit_value", "")
            sub = it.get("sub_value", "")
            sub_label = it.get("sub_label", "")
            main_label = it.get("main_label", "")
            food = it.get("food", "")
            if sub_label and sub != "—":
                value = f"{main_label}/{sub_label}={sub}"
            elif lv and lv != "—":
                value = lv
            else:
                value = "—"
            print(f"  表{tbl} {contam}({symbol}) | {value} | food: {food}")

if own_cnt == 0:
    print("  (空)")

# 2) 推断 ancestorsLevels 段（v82-fix81 后：所有节点显示，过滤 L1 通类 row）
print(f"\nancestorsLevels 段（v82-fix81 后，按上级分类分层显示）：")
print(f"  → '谷物' L2 段（idx 命中 '谷物' L2 节点，过滤 L1 通类）：")
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        a1p_raw = [it.get("a1_l1", ""), it.get("a1_l2", ""),
                   it.get("a1_l3", ""), it.get("a1_l4", "")]
        if a1p_raw[0] in [GRAIN_L1, "谷物及其制品（不包括焙烤制品）"]:
            a1p_raw[0] = GRAIN_L1
        a1p = [x for x in a1p_raw if x]
        # ancestorPath = [GRAIN_L1, "谷物"]
        ancestor_path = [GRAIN_L1, "谷物"]
        if len(a1p) == len(ancestor_path) and a1p == ancestor_path:
            # 过滤 L1 通类
            is_l1_generic = (it.get("a1_l1") and not it.get("a1_l2")
                             and not it.get("a1_l3") and not it.get("a1_l4"))
            if is_l1_generic:
                continue
            # 「除外」过滤（isApplicableToPath）
            food = it.get("food", "")
            if "除外" in food:
                excl_start = food.find("除外")
                excl_end = excl_start
                depth = 0
                for i in range(excl_start - 1, -1, -1):
                    if food[i] in ('）', ')'):
                        depth += 1
                    elif food[i] in ('（', '('):
                        if depth == 0:
                            excl_start = i + 1
                            break
                        depth -= 1
                excl_str = food[excl_start:excl_end]
                exc_list = excl_str.replace('、', ',').replace('，', ',').split(',')
                exc_list = [e.replace('(', '').replace(')', '').replace('（', '').replace('）', '').strip() for e in exc_list]
                damai_match = any("大麦" in e for e in exc_list if len(e) >= 2)
                if damai_match:
                    continue  # 大麦在排除项
            lv = it.get("limit_value", "")
            sub = it.get("sub_value", "")
            sub_label = it.get("sub_label", "")
            main_label = it.get("main_label", "")
            if sub_label and sub != "—":
                value = f"{main_label}/{sub_label}={sub}"
            elif lv and lv != "—":
                value = lv
            else:
                value = "—"
            print(f"    表{tbl} {contam}({symbol}) | {value} | food: {food}")

print(f"\n  → '谷物及其制品' L1 段（过滤 L1 通类 row）：")
for c in contaminants:
    tbl = c.get("table_no")
    contam = c.get("contaminant", "")
    symbol = c.get("symbol", "")
    items = c.get("items", [])
    for idx, it in enumerate(items):
        a1p_raw = [it.get("a1_l1", ""), it.get("a1_l2", ""),
                   it.get("a1_l3", ""), it.get("a1_l4", "")]
        if a1p_raw[0] in [GRAIN_L1, "谷物及其制品（不包括焙烤制品）"]:
            a1p_raw[0] = GRAIN_L1
        a1p = [x for x in a1p_raw if x]
        ancestor_path = [GRAIN_L1]
        if len(a1p) == len(ancestor_path) and a1p == ancestor_path:
            # 过滤 L1 通类
            is_l1_generic = (it.get("a1_l1") and not it.get("a1_l2")
                             and not it.get("a1_l3") and not it.get("a1_l4"))
            if is_l1_generic:
                continue
            # 「除外」过滤
            food = it.get("food", "")
            if "除外" in food:
                excl_start = food.find("除外")
                excl_end = excl_start
                depth = 0
                for i in range(excl_start - 1, -1, -1):
                    if food[i] in ('）', ')'):
                        depth += 1
                    elif food[i] in ('（', '('):
                        if depth == 0:
                            excl_start = i + 1
                            break
                        depth -= 1
                excl_str = food[excl_start:excl_end]
                exc_list = excl_str.replace('、', ',').replace('，', ',').split(',')
                exc_list = [e.replace('(', '').replace(')', '').replace('（', '').replace('）', '').strip() for e in exc_list]
                damai_match = any("大麦" in e for e in exc_list if len(e) >= 2)
                if damai_match:
                    continue
            lv = it.get("limit_value", "")
            print(f"    表{tbl} {contam}({symbol}) | {lv} | food: {food}")