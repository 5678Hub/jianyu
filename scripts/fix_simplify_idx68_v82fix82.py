#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: 简化谷物章节 idx=68 处理（用户「单一简单的思维方式」）

按用户反馈:
- idx=64「麦片、面筋、粥类罐头、带馅(料)面米制品 Pb 0.5」应作为「谷物制品」L2 通类 row
- 删除 idx=65（v82-fix80 复制挂「其他谷物制品」L3 own 段）
- 删除 idx=66（v82-fix79 复制挂「面筋」L4 own 段）

效果:
- 「谷物制品」L2 own 段显示 idx=64（food 含「麦片/面筋/粥类罐头/带馅面米制品」等核心词）
- 「麦片/其他谷物制品/面筋/大米制品/玉米制品/小麦粉制品」等 L3/L4 idx 空节点
  ancestorsLevels 段 fallback 显示 idx=64「谷物制品 L2 通类」row
- 不再有「复制挂 own 段」概念，逻辑完全统一
"""
from pathlib import Path
import json

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

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
c_pb = next(c for c in contaminants if c["contaminant"] == "铅")

# 当前 idx=64-66:
# idx=64 | a1l2=谷物碾磨加工品 a1l3=麦片 a1l4= | food=麦片、面筋、粥类罐头、带馅(料)面米制品
# idx=65 | a1l2=谷物制品 a1l3=其他谷物制品[例如:...粥类罐头等] a1l4= | food=麦片、面筋、粥类罐头、带馅(料)面米制品
# idx=66 | a1l2=谷物制品 a1l3=小麦粉制品 a1l4=面筋 | food=面筋

# 1) 改 idx=64: a1l2='谷物制品' a1l3='' a1l4=''
item_64 = c_pb["items"][64]
print(f"idx=64 修改前: a1l1={item_64.get('a1_l1','')[:20]} a1l2={item_64.get('a1_l2','')} a1l3={item_64.get('a1_l3','')} a1l4={item_64.get('a1_l4','')}")
item_64["a1_l2"] = "谷物制品"
item_64["a1_l3"] = ""
item_64["a1_l4"] = ""
print(f"idx=64 修改后: a1l1={item_64.get('a1_l1','')[:20]} a1l2={item_64.get('a1_l2','')} a1l3={item_64.get('a1_l3','')} a1l4={item_64.get('a1_l4','')}")

# 2) 删 idx=66 (倒序删)
item_66 = c_pb["items"][66]
print(f"\n删除 idx=66: a1l1={item_66.get('a1_l1','')[:20]} a1l2={item_66.get('a1_l2','')} a1l3={item_66.get('a1_l3','')} a1l4={item_66.get('a1_l4','')} | food={item_66.get('food','')[:30]}")
del c_pb["items"][66]

# 3) 删 idx=65 (倒序删, 此时 idx=65 仍指向原 idx=65)
item_65 = c_pb["items"][65]
print(f"删除 idx=65: a1l1={item_65.get('a1_l1','')[:20]} a1l2={item_65.get('a1_l2','')} a1l3={item_65.get('a1_l3','')[:30]} a1l4={item_65.get('a1_l4','')} | food={item_65.get('food','')[:30]}")
del c_pb["items"][65]

print(f"\nPb items: {len(c_pb['items'])}")

# 4) 序列化
new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
src2 = src_text[:start] + new_data_str + src_text[end_idx:]

# 5) bump 版本号
src2 = src2.replace(
    'v82-fix82-revert-fruit-l3-v1-2026-09-02',
    'v82-fix82-simplify-idx68-l2-generic-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"\n完成, 文件大小: {len(src2)} bytes")
print(f"新 MD5: {__import__('hashlib').md5(src2.encode()).hexdigest()}")