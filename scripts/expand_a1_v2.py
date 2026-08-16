#!/usr/bin/env python3
"""
v6.4 — 一次性把 12 张表 251 条 item 的 a1_l1/l2/l3/l4 全部按 A.1 官方树重新展开。

策略:
  - 不保留现有的 L1/L2/L3/L4,统一重做
  - L1:用 item.a1_l1(已对)做锚定,再 expand_a1_full 思路展开 L2/L3/L4
  - food 字段是 source of truth(Sn/Cr/BaP 用户已核对)
  - 失败兜底:保留 L1 only
"""
import json
import re
import sys
from copy import deepcopy

sys.path.insert(0, "scripts")
from expand_a1_full import (
    normalize, short_name, name_variants, node_appears_in,
    find_l1_node, infer_L1_from_food, match_in_tree, AMBIGUOUS_SUFFIXES,
)

JSON_PATH = "data/gb2762/gb2762_2025.json"


def expand_one(item, tree):
    """对单个 item 展开成 a1_l1/l2/l3/l4(只填 1 行)。"""
    food = item.get("food", "") or ""

    # 1. 找 L1
    L1 = item.get("a1_l1", "") or item.get("category_a1", "") or item.get("category", "")
    L1_node = find_l1_node(tree, L1)

    # 如果 item.a1_l1 与官方 A.1 树对不上,尝试 infer
    if not L1_node:
        L1_node = infer_L1_from_food(food, tree)
        if L1_node:
            L1 = L1_node["name"]
        else:
            # 仍找不到,只填 L1
            return L1, "", "", ""

    # 2. 整类条目(以"除外"结尾)→ L1 only
    food_strip = normalize(food).rstrip(")）)")
    if food_strip.endswith("除外") or food_strip.endswith("等除外") or "、除外" in food_strip:
        return L1_node["name"], "", "", ""

    # 3. 在 L1 下找 L2/L3/L4 展开
    matches = match_in_tree(item, L1_node)
    if matches:
        # 取第一个匹配(L2/L3/L4 路径)
        l2, l3, l4 = matches[0]
        # L2 可能等于 L1("谷物及其制品" L1 通类),这种情况清空 L2
        if l2 == L1_node["name"]:
            l2 = ""
        return L1_node["name"], l2, l3, l4

    # 4. fallback L1 only
    return L1_node["name"], "", "", ""


def main():
    d = json.load(open(JSON_PATH, encoding="utf-8"))
    tree = d["appendix_a1"]["tree"]

    total = 0
    changed = 0
    stats = {"L1": 0, "L2": 0, "L3": 0, "L4": 0}

    for c in d["contaminants"]:
        for it in c["items"]:
            total += 1
            l1, l2, l3, l4 = expand_one(it, tree)
            old = (it.get("a1_l1", ""), it.get("a1_l2", ""), it.get("a1_l3", ""), it.get("a1_l4", ""))
            new = (l1, l2, l3, l4)
            it["a1_l1"] = l1
            it["a1_l2"] = l2
            it["a1_l3"] = l3
            it["a1_l4"] = l4
            if old != new:
                changed += 1
            for k, v in zip(("L1", "L2", "L3", "L4"), new):
                if v:
                    stats[k] += 1

    # 写回
    json.dump(d, open(JSON_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"== expand_a1_v2 ==")
    print(f"总条目: {total}")
    print(f"变动: {changed}")
    print(f"完整度: L1={stats['L1']} L2={stats['L2']} L3={stats['L3']} L4={stats['L4']}")
    pct = lambda x: f"{x*100/total:.1f}%"
    print(f"覆盖率: L1={pct(stats['L1'])} L2={pct(stats['L2'])} L3={pct(stats['L3'])} L4={pct(stats['L4'])}")


if __name__ == "__main__":
    main()
