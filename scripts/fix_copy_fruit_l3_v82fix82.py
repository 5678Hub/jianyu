#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: 水果及其制品 7 个 idx 空 L3 节点复制挂载 L2 通类 row

按用户工作流「识别出来一个我确认一个」, 选项 A:
- 「其他新鲜水果(包括甘蔗)」L3: 复制 Pb 新鲜水果(蔓越莓、醋栗除外) + Cd 新鲜水果
- 6 个水果制品 L3(水果罐头/醋、油或盐渍/发酵/煮熟或油炸/水果甜品/其他水果制品):
  复制 Pb 水果制品(果酱...除外) L2 通类 row

按谷物 v82-fix80 成功经验: 复制 idx 后修改 a1_l3 字段。
"""
from pathlib import Path
import json

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

# 1) 解析 inlineData
m = __import__('re').search(r'<script type="application/json" id="inlineData">', src)
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

# 2) 找源 row
def find_row(contam_name, a1l1, a1l2, a1l3=""):
    for c in contaminants:
        if c["contaminant"] != contam_name: continue
        for it in c["items"]:
            if (it.get("a1_l1","") == a1l1 and
                it.get("a1_l2","") == a1l2 and
                it.get("a1_l3","") == a1l3):
                return c, it
    return None, None

# 3) 定义要复制的源 + 目标节点
# 6 个水果制品 L3 节点
fruit_products_l3 = [
    "水果罐头",
    "醋、油或盐渍水果",
    "发酵的水果制品",
    "煮熟的或油炸的水果",
    "水果甜品",
    "其他水果制品",
]

# 1 个新鲜水果 L3 节点
fresh_l3 = "其他新鲜水果（包括甘蔗）"

# 4) 复制逻辑
import copy
inserted = []  # (contam, idx, source_idx, target_node)

# 4.1) Pb 水果制品(果酱...除外) → 6 个 L3
c_pb, src_pb = find_row("铅", "水果及其制品", "水果制品")
assert c_pb is not None, "找不到 Pb 水果制品 L2 通类 row"
src_pb_idx = c_pb["items"].index(src_pb)
for target in fruit_products_l3:
    new_row = copy.deepcopy(src_pb)
    new_row["a1_l3"] = target
    new_row["a1_l4"] = ""
    c_pb["items"].append(new_row)
    inserted.append(("铅", len(c_pb["items"])-1, src_pb_idx, target))

# 4.2) Pb 新鲜水果(蔓越莓、醋栗除外) → 其他新鲜水果（包括甘蔗）L3
c_pb_f, src_pb_f = find_row("铅", "水果及其制品", "新鲜水果（未经加工的、经表面处理的、去皮或预切的、冷冻的水果）")
assert c_pb_f is not None, "找不到 Pb 新鲜水果 L2 通类 row"
src_pb_f_idx = c_pb_f["items"].index(src_pb_f)
new_pb_f = copy.deepcopy(src_pb_f)
new_pb_f["a1_l3"] = fresh_l3
new_pb_f["a1_l4"] = ""
c_pb_f["items"].append(new_pb_f)
inserted.append(("铅", len(c_pb_f["items"])-1, src_pb_f_idx, fresh_l3))

# 4.3) Cd 新鲜水果 → 其他新鲜水果（包括甘蔗）L3
c_cd_f, src_cd_f = find_row("镉", "水果及其制品", "新鲜水果（未经加工的、经表面处理的、去皮或预切的、冷冻的水果）")
assert c_cd_f is not None, "找不到 Cd 新鲜水果 L2 通类 row"
src_cd_f_idx = c_cd_f["items"].index(src_cd_f)
new_cd_f = copy.deepcopy(src_cd_f)
new_cd_f["a1_l3"] = fresh_l3
new_cd_f["a1_l4"] = ""
c_cd_f["items"].append(new_cd_f)
inserted.append(("镉", len(c_cd_f["items"])-1, src_cd_f_idx, fresh_l3))

print(f"已插入 {len(inserted)} 条 row:")
for c, idx, src_idx, target in inserted:
    print(f"  {c} 复制 idx={src_idx} → 挂「{target}」(新 idx={idx})")

# 5) 序列化回 inlineData
new_data_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
# 注: 这会改变缩进风格。让我用 indent=2 保持原风格
new_data_str = json.dumps(data, ensure_ascii=False, indent=2)

# 6) 替换 inlineData JSON
src2 = src_text[:start] + new_data_str + src_text[end_idx:]

# 7) bump 版本号
src2 = src2.replace(
    'v82-fix82-l2-show-l1-fallback-2026-09-02',
    'v82-fix82-copy-fruit-l3-v1-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"\nv82-fix82 fruit 完成, 文件大小: {len(src2)} bytes")
print(f"新 MD5: {__import__('hashlib').md5(src2.encode()).hexdigest()}")