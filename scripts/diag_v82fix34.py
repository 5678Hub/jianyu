# -*- coding: utf-8 -*-
"""v82-fix34 诊断: 检查汞 row 在 inlineData 中的实际结构"""
import os, json, re
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 从 <script type="application/json" id="inlineData"> 提取
m = re.search(r'<script[^>]*id="inlineData"[^>]*>(.*?)</script>', html, re.DOTALL)
if not m:
    print("Cannot find inlineData script tag")
    sys.exit(1)

raw = m.group(1).strip()
print(f"inlineData raw length: {len(raw)} chars")

data = json.loads(raw)
print("inlineData top-level keys:", list(data.keys()))
print(f"contaminants count: {len(data.get('contaminants', []))}")
print(f"appendix_a1 keys: {list(data.get('appendix_a1', {}).keys())}")

tree = data['appendix_a1']['tree']
print(f"\ntree type: {type(tree).__name__}, len: {len(tree)}")
print(f"tree[0] name: {tree[0]['name']}, children count: {len(tree[0].get('children', []))}")

l1_names = [c['name'] for c in tree[0]['children'][:8]]
print(f"前 8 L1: {l1_names}")

# 找 L1 "谷物"
grain_l1 = None
for c in tree[0]['children']:
    if c['name'] == '谷物':
        grain_l1 = c
        break
if grain_l1:
    print(f"\n=== L1 '谷物' children (L2) ===")
    for l2 in grain_l1.get('children', []):
        l2_subs = [l3['name'] for l3 in l2.get('children', [])][:3]
        print(f"  - {l2['name']} (L3 数: {len(l2.get('children', []))}) 示例L3: {l2_subs}")
else:
    print("\nL1 '谷物' 未找到!")

# 汞污染物 rows
print("\n=== 汞 (Hg) items: a1_l1 含'谷物' 的全部 row ===")
for cont in data['contaminants']:
    cname = cont.get('contaminant', '')
    if '汞' not in cname:
        continue
    print(f"\n污染物: {cname} {cont.get('symbol','')} unit={cont.get('unit','')} items数: {len(cont.get('items', []))}")
    for i, item in enumerate(cont.get('items', [])):
        a1_l1 = item.get('a1_l1', '')
        if '谷物' in a1_l1:
            print(f"  [{i}] a1_l1={a1_l1}")
            print(f"      a1_l2={item.get('a1_l2','')}")
            print(f"      a1_l3={item.get('a1_l3','')}")
            print(f"      a1_l4={item.get('a1_l4','')}")
            print(f"      food={item.get('food','')}")
            print(f"      limit={item.get('limit_value','')} has_limit={item.get('has_limit','')}")
