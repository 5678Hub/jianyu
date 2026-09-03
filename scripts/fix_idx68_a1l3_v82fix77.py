#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix77 idx=68 a1_l3 从 '麦片' 改为 '其他谷物制品'，注册到 L3 节点"""
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

for c in data["contaminants"]:
    if c.get("table_no") == 1:
        items = c["items"]
        for it in items:
            if (it.get("food") == "麦片、面筋、粥类罐头、带馅(料)面米制品"
                and it.get("limit_value") == "0.5"):
                old_a1l3 = it["a1_l3"]
                it["a1_l3"] = "其他谷物制品"
                it["a1_l4"] = ""
                print(f"修正 a1_l3: '{old_a1l3}' -> '其他谷物制品'")
                break
        break

# bump 版本注释
if '// v82-fix77' not in src:
    src = re.sub(
        r'(// v82-fix76[^\n]*\n)',
        r'\1// v82-fix77-idx68-a1l3-qita-guwu-zhipin: 修正 idx=68（原）a1_l3 从「麦片」改为「其他谷物制品」，注册到 L3「其他谷物制品」节点（按 GB 2762-2025 附录 A.1 树原位），让「谷物制品」L2 节点 0 限量内容\n',
        src, count=1
    )

new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
new_src = src[:start] + new_json + src[end_idx:]

html_path.write_text(new_src, encoding="utf-8")
print(f"Done. New size: {len(new_src)} bytes")