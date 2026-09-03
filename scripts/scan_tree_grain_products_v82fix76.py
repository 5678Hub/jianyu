#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix76 查询 tree '谷物制品' L2 下子节点"""
import re, json
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

tree = data.get("appendix_a1", {}).get("tree", [])

def walk(nodes, path):
    for n in nodes:
        new_path = path + [n["name"]]
        if "谷物" in n["name"] or "麦片" in n["name"] or "面筋" in n["name"]:
            print(f"  {' > '.join(new_path)}")
            if n.get("children"):
                print(f"    children({len(n['children'])}): {[c['name'] for c in n['children']]}")
            else:
                print(f"    (no children)")

print("=== 树中含「谷物/麦片/面筋」的节点 ===")
walk(tree, [])
print()

# 找「谷物制品」L2
def find_node(nodes, target, path):
    for n in nodes:
        new_path = path + [n["name"]]
        if n["name"] == target:
            return new_path, n
        if n.get("children"):
            found = find_node(n["children"], target, new_path)
            if found:
                return found
    return None

result = find_node(tree, "谷物制品", [])
if result:
    p, n = result
    print(f"=== {' > '.join(p)} ===")
    print(f"  children({len(n.get('children', []))}):")
    for c in n.get("children", []):
        print(f"    - {c['name']}")
else:
    print("找不到 '谷物制品' 节点")

result2 = find_node(tree, "麦片", [])
if result2:
    p, n = result2
    print(f"=== {' > '.join(p)} ===")
    print(f"  children({len(n.get('children', []))}): {[c['name'] for c in n.get('children', [])]}")
else:
    print("找不到 '麦片' 节点")