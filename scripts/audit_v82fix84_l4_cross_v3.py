"""v82-fix84 L4 跨 L3 显示模拟 v3 - 修正 ancestorsLevels L3 段判定逻辑

ancestorsLevels L3 段 (idx.get(L3 pathKey)) 只返回 pathKey L3 + a1l4=path.l4 注册的 row
跨 L4 兄弟 row 不在该段显示, 因此 v82-fix84 应该收集所有 a1l3=path.l3, a1l4!=path.l4, a1l4!='' 的 row
"""
import json
import re

with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

def norm(s):
    if not s:
        return ''
    s = str(s)
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】+]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s

# 注册 idx (按 norm path_key)
idx = {}
for con in d['contaminants']:
    for it in con['items']:
        parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
        pk = '|'.join([norm(p) for p in parts if p])
        if pk:
            idx.setdefault(pk, []).append((con['table_no'], con['contaminant'], it))

# 收集所有 L4 节点
tree = d['appendix_a1']['tree']
all_l4 = []
for root in tree:
    for c2 in root.get('children', []):
        for c3 in c2.get('children', []):
            for c4 in c3.get('children', []):
                all_l4.append((root['name'], c2['name'], c3['name'], c4['name']))

empty_l4 = []
for path in all_l4:
    pk = '|'.join(norm(p) for p in path)
    if not idx.get(pk):
        empty_l4.append(path)

print(f'Tree L4 节点总数: {len(all_l4)}')
print(f'L4 idx 真空节点: {len(empty_l4)} 个')
print()

# 修正: ancestorsLevels L3 段只显示 pathKey L3 = ancestorKey + a1l4=path.l4 注册的 row
# 跨 L4 兄弟 row 不在 ancestorsLevels L3 段显示, v82-fix84 应该收集它们
total_cross = 0
for path in empty_l4:
    l1, l2, l3, l4 = path

    # 找跨 L4 兄弟 row: a1l1=l1, a1l2=l2, a1l3=l3, a1l4!=l4, a1l4!='' 的 row
    cross_l4_rows = []
    for k, rows in idx.items():
        for tno, pol, it in rows:
            if (norm(it.get('a1_l1','')) == norm(l1) and
                norm(it.get('a1_l2','')) == norm(l2) and
                norm(it.get('a1_l3','')) == norm(l3) and
                it.get('a1_l4','') and norm(it.get('a1_l4','')) != norm(l4)):
                cross_l4_rows.append((tno, pol, it))

    if cross_l4_rows:
        total_cross += len(cross_l4_rows)
        print(f'\n[L4] {l4[:35]} ({l1[:10]} / {l2[:15]} / {l3[:15]})')
        print(f'  跨 L4 兄弟 row ({len(cross_l4_rows)} 条):')
        for tno, pol, it in cross_l4_rows:
            lv = it.get('limit_value','')
            sv = it.get('sub_value','')
            food = it.get('food','')
            modif = it.get('modif','')
            a4 = it.get('a1_l4','')
            print(f'    [{tno}{pol}] val={lv}{("/"+sv) if sv else ""} {food[:35]} (L4挂载: {a4[:40]})')
            if modif:
                print(f'         modif: {modif}')

print(f'\n\n=== 总计跨 L4 兄弟 row: {total_cross} 条 ===')
