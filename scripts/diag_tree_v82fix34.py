# -*- coding: utf-8 -*-
import os, json, re
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script[^>]*id="inlineData"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1).strip())

tree = data['appendix_a1']['tree']
print(f"tree type: {type(tree).__name__}, len: {len(tree)}")
print("\n=== tree 顶层 23 个节点 (实际是 L1) ===")
for i, n in enumerate(tree):
    name = n.get('name', '?')
    children = n.get('children', [])
    sub_count = len(children)
    sub_names = [c['name'] for c in children[:5]]
    print(f"[{i}] {name} (子数={sub_count}) 前5子: {sub_names}")

# 找名为 '谷物' 的节点
print("\n=== 找 '谷物' 节点 ===")
def find_node(nodes, target, path=[]):
    results = []
    for n in nodes:
        if n.get('name') == target:
            results.append((path + [n.get('name')], n))
        if n.get('children'):
            results.extend(find_node(n['children'], target, path + [n.get('name')]))
    return results

found = find_node(tree, '谷物')
for path, n in found:
    print(f"路径: {' > '.join(path)}")
    print(f"  children 数: {len(n.get('children', []))}")
    for c in n.get('children', []):
        print(f"    - L2: {c['name']} (子数={len(c.get('children', []))})")
        for c2 in c.get('children', [])[:3]:
            print(f"        - L3: {c2['name']}")

# 找 '谷物及其制品' 节点
print("\n=== 找 '谷物及其制品' (任意前缀) 节点 ===")
found = find_node(tree, '谷物及其制品（不包括焙烤制品）')
for path, n in found:
    print(f"路径: {' > '.join(path)}")
    print(f"  children 数: {len(n.get('children', []))}")
