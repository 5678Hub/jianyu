#!/usr/bin/env python3
"""v82-fix42: L3 熟制坚果及籽类（带壳、脱壳、包衣）添加 2 条 row

用户截图显示参考值（来自 L2 生干坚果及籽类）：
  - 铅 Pb 生咖啡豆及烘焙咖啡豆 ≤0.5 mg/kg GB 5009.12 (d)
  - 镉 Cd 花生 ≤0.5 mg/kg GB 5009.15 (b)

用户要求：「添加截图中的内容」到 L3 熟制坚果及籽类（带壳、脱壳、包衣）。

按 L3 类目作为 food 名添加（语义合理：L3 自身有限量值）：
  - 铅: food=熟制坚果及籽类（带壳、脱壳、包衣）, limit=0.5, method=GB 5009.12, note=d
  - 镉: food=熟制坚果及籽类（带壳、脱壳、包衣）, limit=0.5, method=GB 5009.15, note=b
"""
import json
import sys
from pathlib import Path

FILE = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
BACKSLASH = chr(92); QUOTE = chr(34)

html = FILE.read_text(encoding="utf-8")
start_tag = '<script type="application/json" id="inlineData">'
end_tag = '</script>'
start = html.index(start_tag) + len(start_tag)
depth = 0; in_str = False; esc = False; obj_end = -1
for off in range(start, len(html)):
    ch = html[off]
    if in_str:
        if esc: esc = False
        elif ch == BACKSLASH: esc = True
        elif ch == QUOTE: in_str = False
        continue
    if ch == QUOTE: in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = off + 1; break
if obj_end == -1:
    sys.exit("ERROR: inlineData JSON not found")

raw_json = html[start:obj_end]
data = json.loads(raw_json)

L3_NAME = "熟制坚果及籽类（带壳、脱壳、包衣）"
L2_NAME = "坚果及籽类制品"
L1_NAME = "坚果及籽类"

# 找下一个可用 rXXXX id（用于新 row，不影响现有索引逻辑）
max_idx = 0
def walk_max_idx(node):
    global max_idx
    if isinstance(node, dict):
        if isinstance(node.get("id"), str) and node["id"].startswith("r"):
            try:
                n = int(node["id"][1:])
                if n > max_idx: max_idx = n
            except ValueError:
                pass
        for v in node.values():
            walk_max_idx(v)
    elif isinstance(node, list):
        for v in node:
            walk_max_idx(v)
walk_max_idx(data)
print(f"Max r-id in data: r{max_idx:04d}")

added = []
for sym, method, note in [
    ("Pb", "GB 5009.12", "d"),
    ("Cd", "GB 5009.15", "b"),
]:
    contam = next((c for c in data["contaminants"] if c.get("symbol") == sym), None)
    if contam is None:
        print(f"  WARN: contaminant {sym} not found")
        continue
    max_idx += 1
    new_id = f"r{max_idx:04d}"
    # limit 单位：与原 L2 参考行一致
    new_row = {
        "id": new_id,
        "food": L3_NAME,
        "pollutant": {"Pb": "铅", "Cd": "镉"}[sym],
        "limit_value": "0.5",
        "has_limit": True,
        "sub_value": "",
        "unit": "mg/kg",
        "note": note,
        "modif": "",
        "inspection_method": method,
        "a1_l1": L1_NAME,
        "a1_l2": L2_NAME,
        "a1_l3": L3_NAME,
        "a1_l4": "",
    }
    contam["items"].append(new_row)
    added.append((sym, new_id))
    print(f"  Added {sym} row: id={new_id}, food={L3_NAME}, limit=0.5, note={note}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处
OLD_META = "v82-fix41-beverage-pdf-hier-2026-09-01"
NEW_META = "v82-fix42-nut-cooked-pb-cd-2026-09-01"
OLD_TITLE = "[v82-fix41]"
NEW_TITLE = "[v82-fix42]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places; title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")