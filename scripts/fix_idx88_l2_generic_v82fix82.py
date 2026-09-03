#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: idx=88 改为「谷物制品」L2 通类 row

原因: 用户反馈「面筋」L4 节点 ancestorsLevels 段看不到上层 row。
根因: idx=88 (复制 idx=64) 挂「其他谷物制品」L3 own 段, ancestorsLevels 段 i=1 查「谷物制品」L2 pk 时 idx=0。

修复: idx=88 a1l3='' a1l4='' 改为 L2 通类 row, 注册到「谷物制品」L2 own 段。
- 「面筋」L4 节点 ancestorsLevels 段 i=1 命中 idx=88 → 显示「谷物制品 L2 通类」Pb row ✅
- 「其他谷物制品」L3 节点 own 段变空, ancestorsLevels 段 i=1 命中 idx=88 fallback ✅
  (与「水果罐头」一致: idx 空 → ancestorsLevels fallback)

idx=89 (面筋 L4 own row) 保留不变。
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

# 找 idx=88: a1l2='谷物制品' a1l3='其他谷物制品[...]'
target_idx = None
for i, it in enumerate(c_pb["items"]):
    if (it.get('a1_l1','') == '谷物及其制品（不包括焙烤制品）' and
        it.get('a1_l2','') == '谷物制品' and
        '其他谷物制品' in it.get('a1_l3','')):
        target_idx = i
        break

print(f"找到 idx={target_idx}: a1l3={c_pb['items'][target_idx].get('a1_l3','')[:30]}")
c_pb["items"][target_idx]["a1_l3"] = ""
c_pb["items"][target_idx]["a1_l4"] = ""
print(f"修改后: a1l3='' a1l4=''")

new_data_str = json.dumps(data, ensure_ascii=False, indent=2)
src2 = src_text[:start] + new_data_str + src_text[end_idx:]

src2 = src2.replace(
    'v82-fix82-restore-grain-multi-mount-2026-09-02',
    'v82-fix82-idx88-l2-generic-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"\n完成, 文件大小: {len(src2)} bytes")
print(f"新 MD5: {__import__('hashlib').md5(src2.encode()).hexdigest()}")