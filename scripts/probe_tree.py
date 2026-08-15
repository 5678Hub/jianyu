import json

with open('data/gb2762/gb2762_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

tree = data['appendix_a1']['tree']
print(f"现有 L1 大类数: {len(tree)}")
for n in tree:
    print(f"  - {n['name']}")

# 扫描含"包装饮用水"的条目
print("\n=== 含'包装饮用水'的条目 ===")
for tab in data['contaminants']:
    for it in tab['items']:
        food = it.get('food', '') or ''
        a1l4 = it.get('a1_l4', '') or ''
        a1l3 = it.get('a1_l3', '') or ''
        a1l2 = it.get('a1_l2', '') or ''
        a1l1 = it.get('a1_l1', '') or ''
        if '包装饮用水' in food or '包装饮用水' in a1l4 or '包装饮用水' in a1l3 or '包装饮用水' in a1l2:
            print(f"  表{tab.get('table_no')} {tab.get('contaminant')} food={food!r} L1={a1l1} L2={a1l2} L3={a1l3} L4={a1l4}")

# 表 9 当前 a 脚注分布
print("\n=== 表 9 当前脚注分布 ===")
for tab in data['contaminants']:
    if tab.get('table_no') == 9:
        for i, it in enumerate(tab['items']):
            print(f"  [{i}] L3={it.get('a1_l3','')!r}  footnote={it.get('remark','')!r}")