#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix76 模拟 matchItemToPaths 看 idx=68 注册到哪些 path"""
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

# 找 idx=68 row
for c in data["contaminants"]:
    if c.get("table_no") == 1:
        for idx, it in enumerate(c["items"]):
            if (it.get("food") == "麦片、面筋、粥类罐头、带馅(料)面米制品"
                and it.get("limit_value") == "0.5"):
                print(f"找到 idx={idx}")
                print(f"  food: {it.get('food')}")
                print(f"  a1_l1: {it.get('a1_l1')}")
                print(f"  a1_l2: {it.get('a1_l2')}")
                print(f"  a1_l3: {it.get('a1_l3')}")
                print(f"  a1_l4: {it.get('a1_l4')}")
                print()

# 在浏览器中执行 matchItemToPaths，看注册到哪些 path
# 由于 Python 不能直接跑 JS，我们推理：
# a1_l3='麦片' 在 tree '谷物制品' L2 children 中找不到
# → Fallback B: 注册到 '谷物制品' L2 pathKey
print("=== 推理 idx=68 注册结果 ===")
print("a1Path = ['谷物及其制品（不包括焙烤制品）', '谷物制品', '麦片']")
print("walkExact 走完：")
print("  1. 找 L1 '谷物及其制品（不包括焙烤制品）' → 找到")
print("  2. 找 L2 '谷物制品' → 找到")
print("  3. 找 L3 '麦片' in children('大米制品/小麦粉制品/玉米制品/其他谷物制品') → 找不到")
print("  4. Fallback B: !matchedHere + idx===a1Path.length-1 + path.length>0")
print("     → 注册到 '谷物及其制品（不包括焙烤制品）|谷物制品' (L2 '谷物制品')")
print()
print("=== 推论 ===")
print("'谷物制品' L2 节点 idx 命中 = [idx=68]，显示 1 条 own row")
print("'其他谷物制品' L3 idx 空节点 ancestorsLevels 段显示 idx=68 Pb 0.5")