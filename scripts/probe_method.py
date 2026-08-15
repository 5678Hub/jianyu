import json
with open('data/gb2762/gb2762_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for tab in data['contaminants']:
    if tab.get('table_no') in (1, 4):
        print(f"=== 表{tab.get('table_no')} {tab.get('contaminant')} 表级 inspection_method={tab.get('inspection_method','')!r} ===")
        for it in tab['items']:
            if '包装饮用水' in it.get('a1_l2','') or '包装饮用水' in it.get('food',''):
                if '除外' not in it.get('food',''):
                    print(f"  food={it.get('food','')!r} a1_l2={it.get('a1_l2','')!r}")
                    print(f"  item.inspection_method={it.get('inspection_method','')!r}")
                    print(f"  item.test_method={it.get('test_method','')!r}")