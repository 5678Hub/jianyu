#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix80 修正 idx=68 多节点复制挂「麦片」L3 + 「其他谷物制品」L3"""
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
        # 找 idx=68 主 row（food='麦片、面筋、粥类罐头、带馅(料)面米制品'）
        main_idx = None
        for idx, it in enumerate(items):
            if (it.get("food") == "麦片、面筋、粥类罐头、带馅(料)面米制品"
                and it.get("limit_value") == "0.5"
                and it.get("a1_l3") == "其他谷物制品"):
                main_idx = idx
                break

        if main_idx is None:
            print("[err] idx=68 主 row (a1_l3='其他谷物制品') not found")
            sys.exit(1)

        # 1. 改 main_idx 的 a1_l2/a1_l3 为「麦片」L3 节点
        items[main_idx]["a1_l2"] = "谷物碾磨加工品"
        items[main_idx]["a1_l3"] = "麦片"
        items[main_idx]["a1_l4"] = ""
        print(f"修正 main_idx={main_idx}: a1_l2='谷物碾磨加工品' a1_l3='麦片'")

        # 2. 在 main_idx 后插入 2 个复制
        # 2a. 挂「其他谷物制品」L3 节点（合并表达入口 row）
        row_other = copy.deepcopy(items[main_idx])
        row_other["a1_l2"] = "谷物制品"
        row_other["a1_l3"] = "其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]"
        row_other["a1_l4"] = ""
        items.insert(main_idx + 1, row_other)
        print(f"插入 idx={main_idx+1}: a1_l2='谷物制品' a1_l3='其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]'")

        # 2b. 挂「面筋」L4 节点（v82-fix79 已经有了，但要确保 a1_l3 是「小麦粉制品」）
        # v82-fix79 已加，不需要再加

        print(f"Pb 表: {len(items)} 条")
        break

# bump 版本注释
if '// v82-fix80' not in src:
    src = re.sub(
        r'(// v82-fix79[^\n]*\n)',
        r'\1// v82-fix80-idx68-multi-mount: idx=68「麦片、面筋、粥类罐头、带馅(料)面米制品 0.5」按多节点复制风格挂「麦片」L3（谷物碾磨加工品）+「其他谷物制品」L3（合并表达入口）+「面筋」L4（v82-fix79 已加）\n',
        src, count=1
    )

new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
new_src = src[:start] + new_json + src[end_idx:]

html_path.write_text(new_src, encoding="utf-8")
print(f"Done. New size: {len(new_src)} bytes")