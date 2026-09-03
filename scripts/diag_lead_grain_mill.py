# -*- coding: utf-8 -*-
"""查 L2 谷物碾磨加工品下的铅 row + L3 子节点名"""
import os, json, re
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script[^>]*id="inlineData"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1).strip())
tree = data['appendix_a1']['tree']

# 找 L1 谷物及其制品
grain_l1 = None
for n in tree:
    if '谷物及其制品' in n['name']:
        grain_l1 = n
        break

# L2 谷物碾磨加工品
mill_l2 = None
for l2 in grain_l1.get('children', []):
    if '谷物碾磨加工品' in l2['name']:
        mill_l2 = l2
        break

print(f"L1: {grain_l1['name']}")
print(f"L2 谷物碾磨加工品 children (L3):")
for l3 in mill_l2.get('children', []):
    has_l4 = bool(l3.get('children'))
    print(f"  - {l3['name']} (有L4={has_l4})")

# 铅污染物 a1_l1 含谷物 的所有 row
print("\n=== 铅 Pb items: a1_l1='谷物及其制品' 全部 row ===")
for cont in data['contaminants']:
    if '铅' not in cont.get('contaminant', '') and 'Pb' not in cont.get('symbol', ''):
        continue
    print(f"\n污染物: {cont.get('contaminant','')} {cont.get('symbol','')} unit={cont.get('unit','')} items数: {len(cont.get('items', []))}")
    for i, item in enumerate(cont.get('items', [])):
        a1_l1 = item.get('a1_l1', '')
        if '谷物' in a1_l1:
            print(f"  [{i}] a1_l1={a1_l1}")
            print(f"      a1_l2={item.get('a1_l2','')!r}")
            print(f"      a1_l3={item.get('a1_l3','')!r}")
            print(f"      a1_l4={item.get('a1_l4','')!r}")
            print(f"      food={item.get('food','')}")
            print(f"      limit={item.get('limit_value','')} has_limit={item.get('has_limit','')}")
