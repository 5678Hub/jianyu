#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 修正 idx=68 a1_l2 从「谷物碾磨加工品」改为「谷物制品」"""
import re, json, sys
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
i = m.end()
depth = 0; start = i
while i < len(src):
    if src[i] == '{': depth += 1
    elif src[i] == '}':
        depth -= 1
        if depth == 0: break
    i += 1
end = i + 1
data = json.loads(src[start:end])

for c in data["contaminants"]:
    if c.get("table_no") == 1:
        items = c["items"]
        # 找 idx=68（原）即现在 position=64 food='麦片、面筋、粥类罐头、带馅(料)面米制品'
        for it in items:
            if (it.get("food") == "麦片、面筋、粥类罐头、带馅(料)面米制品"
                and it.get("limit_value") == "0.5"):
                old_a1l2 = it["a1_l2"]
                it["a1_l2"] = "谷物制品"
                print(f"修正 idx(原68) a1_l2: '{old_a1l2}' -> '谷物制品'")
                break
        break

# bump 版本注释
if '// v82-fix76' not in src:
    src = re.sub(
        r'(// v82-fix75[^\n]*\n)',
        r'\1// v82-fix76-fix-idx68-a1l2: 修正 idx=68（原）a1_l2 从「谷物碾磨加工品」改为「谷物制品」（按 GB 2762-2025 附录 A.1 分类树原位）\n',
        src, count=1
    )

new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
new_src = src[:start] + new_json + src[end:]

html_path.write_text(new_src, encoding="utf-8")
print(f"Done. New size: {len(new_src)} bytes")