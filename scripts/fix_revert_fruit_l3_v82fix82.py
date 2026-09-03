#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: 撤回水果及其制品 8 条 row 复制挂载（用户反馈错误）

撤回 v82-fix82-copy-fruit-l3-v1 的 8 条 row:
- 6 条 Pb 复制 (idx=90-95) 挂水果制品 L3
- 1 条 Pb 复制 (idx=96) + 1 条 Cd 复制 (idx=49) 挂「其他新鲜水果(包括甘蔗)」L3

撤回原因: 「水果罐头」PDF 原文未专门写 row, 应当走 ancestorsLevels 段
显示「水果制品 L2 通类」fallback, 而不是 own 段复制挂载。
"""
from pathlib import Path
import json

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

# 1) 解析 inlineData
m = __import__('re').search(r'<script type=\"application/json\" id=\"inlineData\">', src)
i = m.end(); depth = 0; start = i; end_idx = i
src_text = src
while i < len(src_text):
    if src_text[i] == '{': depth += 1
    elif src_text[i] == '}':
        depth -= 1
        if depth == 0: end_idx = i + 1; break
    i += 1
data = json.loads(src_text[start:end_idx])

contaminants = data["contaminants"]

# 2) 找到要删除的 row (按 a1_l1 + a1_l3 匹配)
def remove_rows(contam_name, a1l1, a1l3_targets):
    """删除污染物 a1l1 + a1l3 匹配的行"""
    removed = []
    for c in contaminants:
        if c["contaminant"] != contam_name: continue
        new_items = []
        for it in c["items"]:
            if (it.get("a1_l1","") == a1l1 and
                it.get("a1_l3","") in a1l3_targets):
                removed.append({"contam": contam_name, "food": it.get("food","")[:40],
                               "a1l3": it.get("a1_l3","")})
            else:
                new_items.append(it)
        c["items"] = new_items
    return removed

# 6 个水果制品 L3 节点(挂 Pb 复制)
removed_pb_fruit = remove_rows("铅", "水果及其制品",
    ["水果罐头", "醋、油或盐渍水果", "发酵的水果制品",
     "煮熟的或油炸的水果", "水果甜品", "其他水果制品"])

# 其他新鲜水果(包括甘蔗) L3 节点(挂 Pb + Cd 复制)
removed_pb_fresh = remove_rows("铅", "水果及其制品", ["其他新鲜水果（包括甘蔗）"])
removed_cd_fresh = remove_rows("镉", "水果及其制品", ["其他新鲜水果（包括甘蔗）"])

all_removed = removed_pb_fruit + removed_pb_fresh + removed_cd_fresh
print(f"已撤回 {len(all_removed)} 条 row:")
for r in all_removed:
    print(f"  - {r['contam']} {r['a1l3']}: {r['food']}")

# 3) 序列化
new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
src2 = src_text[:start] + new_data_str + src_text[end_idx:]

# 4) bump 版本号
src2 = src2.replace(
    'v82-fix82-copy-fruit-l3-v1-2026-09-02',
    'v82-fix82-revert-fruit-l3-v1-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"\n撤回完成, 文件大小: {len(src2)} bytes")
print(f"新 MD5: {__import__('hashlib').md5(src2.encode()).hexdigest()}")