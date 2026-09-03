#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix79 复制 idx=68 挂「面筋」L4 节点"""
import re, json, copy, sys
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

for c in data["contaminants"]:
    if c.get("table_no") == 1:
        items = c["items"]
        # 找 idx=68 row（现在 position 因为 v82-fix75 删了 4 条变成 64）
        target_idx = None
        for idx, it in enumerate(items):
            if (it.get("food") == "麦片、面筋、粥类罐头、带馅(料)面米制品"
                and it.get("limit_value") == "0.5"):
                target_idx = idx
                break

        if target_idx is None:
            print("[err] idx=68 not found")
            sys.exit(1)

        src_row = items[target_idx]
        new_row = copy.deepcopy(src_row)
        new_row["food"] = "面筋"
        new_row["a1_l1"] = "谷物及其制品（不包括焙烤制品）"
        new_row["a1_l2"] = "谷物制品"
        new_row["a1_l3"] = "小麦粉制品"
        new_row["a1_l4"] = "面筋"
        items.insert(target_idx + 1, new_row)
        print(f"复制 idx={target_idx} 到 idx={target_idx+1}:")
        print(f"  food: {new_row['food']}")
        print(f"  a1_l1: {new_row['a1_l1']}")
        print(f"  a1_l2: {new_row['a1_l2']}")
        print(f"  a1_l3: {new_row['a1_l3']}")
        print(f"  a1_l4: {new_row['a1_l4']}")
        print(f"Pb 表: {len(items)} 条")
        break

# bump 版本注释
if '// v82-fix79' not in src:
    src = re.sub(
        r'(// v82-fix78[^\n]*\n)',
        r'\1// v82-fix79-copy-idx68-mianjin: 复制 idx=68「麦片、面筋、粥类罐头、带馅(料)面米制品 0.5」挂「面筋」L4 节点（按 GB 2762-2025 附录 A.1 树中「面筋」是「小麦粉制品」下 L4）\n',
        src, count=1
    )

new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
new_src = src[:start] + new_json + src[end_idx:]

html_path.write_text(new_src, encoding="utf-8")
print(f"Done. New size: {len(new_src)} bytes")