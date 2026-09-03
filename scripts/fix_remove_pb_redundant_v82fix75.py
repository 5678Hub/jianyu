#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix75 删 Pb idx=64-67 4 条画蛇添足 row"""
import re, json, sys
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

m = re.search(r'<script type="application/json" id="inlineData">', src)
if not m:
    print("[err] inlineData not found")
    sys.exit(1)

i = m.end()
depth = 0
start = i
while i < len(src):
    ch = src[i]
    if ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            break
    i += 1

end = i + 1
data = json.loads(src[start:end])

# 找 Pb 表（table_no=1）
contaminants = data["contaminants"]
removed = []
for c in contaminants:
    if c.get("table_no") == 1:
        items = c["items"]
        # 检查 idx=64-67 内容
        for i in [64, 65, 66, 67]:
            if i < len(items):
                it = items[i]
                print(f"  [idx={i}] {it.get('food','')[:30]} | {it.get('a1_l1','')[:20]} | {it.get('a1_l3','')[:20]} | {it.get('limit_value','')}")
        # 确认是 Pb 谷物章节后，从 position 64 开始删 4 条
        # 但需要先验证 idx=64 是「糙米」（a1_l3='糙米（包括色稻米）'）
        before = len(items)
        # 删 idx=64,65,66,67 (位置索引，从0开始)
        # 验证
        target_text = "谷物碾磨加工品"
        if items[64].get("a1_l2") == target_text and items[67].get("a1_l2") == target_text:
            del items[64:68]
            after = len(items)
            removed = before - after
            print(f"Pb 表：{before} 条 -> {after} 条（删 {removed} 条）")
        else:
            print("[err] idx=64-67 不是谷物碾磨加工品下的 row")
            sys.exit(1)
        break

# bump 版本注释
new_src = src
if '// v82-fix75' not in new_src:
    # 在最近的 v82-fix74 后插入
    new_src = re.sub(
        r'(// v82-fix74[^\n]*\n)',
        r'\1// v82-fix75-remove-pb-grain-redundant-rows: 删 Pb idx=64-67（糙米/大米/小麦粉/玉米粉 4 条画蛇添足，PDF 表 1 谷物章节只 2 行）\n',
        new_src, count=1
    )

# 写回 inlineData
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
new_src = new_src[:start] + new_json + new_src[end:]

html_path.write_text(new_src, encoding="utf-8")
print(f"Done. New size: {len(new_src)} bytes")
print(f"Removed {removed} Pb rows")