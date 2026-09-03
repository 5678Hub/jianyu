#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: 撤回 idx=88 L2 通类改动, 恢复 v82-fix80 多节点挂载

按用户最新反馈:
- 「谷物制品」L2 节点 own 段应空(不该是「本级」, PDF 原文在 L2 章节没写这条 row)
- 「麦片/其他谷物制品/面筋」L3/L4 节点 own 段应显示(他们是 PDF 原文覆盖目标)
- idx=88 (谷物制品 L2 通类) 撤回, 改为 idx=65 挂「其他谷物制品」L3
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

# 1) 找 idx=88 (谷物制品 L2 通类 a1l2='谷物制品' a1l3='' a1l4='')
# 撤回：删除
target_88_idx = None
for i, it in enumerate(c_pb["items"]):
    if (it.get('a1_l1','') == '谷物及其制品（不包括焙烤制品）' and
        it.get('a1_l2','') == '谷物制品' and
        not it.get('a1_l3','') and
        not it.get('a1_l4','')):
        target_88_idx = i
        break

print(f"删除 idx={target_88_idx}: {c_pb['items'][target_88_idx].get('food','')[:30]}")
del c_pb["items"][target_88_idx]

# 2) 找 idx=64 (谷物碾磨加工品/麦片 L3 own row), 复制一份挂「其他谷物制品」L3
idx_64 = c_pb["items"][64]
print(f"\n参考 idx=64: a1l2={idx_64.get('a1_l2','')} a1l3={idx_64.get('a1_l3','')} a1l4={idx_64.get('a1_l4','')}")

import copy
new_65 = copy.deepcopy(idx_64)
new_65["a1_l2"] = "谷物制品"
new_65["a1_l3"] = "其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]"
new_65["a1_l4"] = ""
c_pb["items"].append(new_65)
print(f"插入 idx={len(c_pb['items'])-1}: a1l2={new_65.get('a1_l2','')} a1l3={new_65.get('a1_l3','')[:30]} a1l4={new_65.get('a1_l4','')}")

print(f"\nPb items: {len(c_pb['items'])}")

# 3) 序列化
new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
src2 = src_text[:start] + new_data_str + src_text[end_idx:]

# 4) bump 版本号
src2 = src2.replace(
    'v82-fix82-dedup-viasub-2026-09-02',
    'v82-fix82-revert-idx88-multi-mount-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"\n完成, 文件大小: {len(src2)} bytes")
print(f"新 MD5: {__import__('hashlib').md5(src2.encode()).hexdigest()}")