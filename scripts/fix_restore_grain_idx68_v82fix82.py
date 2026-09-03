#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: 恢复 v82-fix79/80 谷物章节 idx=64 多节点复制挂载

按用户最新反馈:
- 「麦片/面筋/其他谷物制品都有自己的限量要求啊, 引用就是引用」
- idx=64 「麦片、面筋、粥类罐头、带馅(料)面米制品 Pb 0.5」是 PDF 原文覆盖 row
- 应复制挂「其他谷物制品」L3 + 「面筋」L4 own 段
- idx=64 主 row 改回挂「麦片」L3 own 段(原 v82-fix80 状态)

撤回刚做的「简化」改回多节点挂载
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

# 当前 idx=64 (简化后挂「谷物制品」L2 通类)
item_64 = c_pb["items"][64]
print(f"idx=64 修改前: a1l2={item_64.get('a1_l2','')} a1l3={item_64.get('a1_l3','')} a1l4={item_64.get('a1_l4','')}")

# 1) 改 idx=64 主 row: 挂「谷物碾磨加工品」→「麦片」L3 own 段
item_64["a1_l2"] = "谷物碾磨加工品"
item_64["a1_l3"] = "麦片"
item_64["a1_l4"] = ""
print(f"idx=64 修改后: a1l2={item_64.get('a1_l2','')} a1l3={item_64.get('a1_l3','')} a1l4={item_64.get('a1_l4','')}")

# 2) 复制 idx=64 → 挂「其他谷物制品」L3
import copy
new_65 = copy.deepcopy(item_64)
new_65["a1_l2"] = "谷物制品"
new_65["a1_l3"] = "其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]"
new_65["a1_l4"] = ""
c_pb["items"].append(new_65)
print(f"插入 idx={len(c_pb['items'])-1}: a1l2={new_65.get('a1_l2','')} a1l3={new_65.get('a1_l3','')[:30]} a1l4={new_65.get('a1_l4','')}")

# 3) 复制 idx=64 → 挂「小麦粉制品」→「面筋」L4
new_66 = copy.deepcopy(item_64)
new_66["a1_l2"] = "谷物制品"
new_66["a1_l3"] = "小麦粉制品"
new_66["a1_l4"] = "面筋"
c_pb["items"].append(new_66)
print(f"插入 idx={len(c_pb['items'])-1}: a1l2={new_66.get('a1_l2','')} a1l3={new_66.get('a1_l3','')} a1l4={new_66.get('a1_l4','')}")

print(f"\nPb items: {len(c_pb['items'])}")

# 4) 序列化
new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
src2 = src_text[:start] + new_data_str + src_text[end_idx:]

# 5) bump 版本号
src2 = src2.replace(
    'v82-fix82-simplify-idx68-l2-generic-2026-09-02',
    'v82-fix82-restore-grain-multi-mount-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"\n完成, 文件大小: {len(src2)} bytes")
print(f"新 MD5: {__import__('hashlib').md5(src2.encode()).hexdigest()}")