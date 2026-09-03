"""v82-fix84 L4 跨 L3 显示模拟 - 列出每个 L4 idx 空节点的「跨了哪些 row」给用户核对"""
import json
import re

with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

def norm(s):
    if not s:
        return ''
    s = str(s)
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s

def path_key(parts):
    return '|'.join([norm(p) for p in parts if p])

# 注册 idx
idx = {}
for con in d['contaminants']:
    for it in con['items']:
        parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
        pk = path_key(parts)
        if pk:
            idx.setdefault(pk, []).append((con['table_no'], con['contaminant'], it))

# 收集所有 L4 节点
tree = d['appendix_a1']['tree']
all_l4 = []
def walk(node, path, depth):
    new_path = path + [node['name']]
    if depth == 4:
        all_l4.append(tuple(new_path))
        return
    if depth >= 4:
        return
    for c in node.get('children', []):
        walk(c, new_path, depth + 1)

for n in tree:
    walk(n, [], 0)

# 找 L4 idx 空节点
empty_l4 = []
for path in all_l4:
    pk = path_key(path)
    if not idx.get(pk):
        empty_l4.append(path)

print(f'L4 idx 真空节点: {len(empty_l4)} 个')
print()

# 对每个 L4 idx 空节点, 列出「跨 L4 兄弟 row」(v82-fix84 新加)
total_cross = 0
for path in empty_l4:
    l1, l2, l3, l4 = path
    pk_l4 = path_key([l1, l2, l3, l4])
    pk_l3 = path_key([l1, l2, l3])
    pk_l2 = path_key([l1, l2])
    pk_l1 = path_key([l1])

    # ancestorsLevels 段已显示的 row: L3 own (含 a1l3=l3 的 row) + L2 通类 + L1 通类
    ancestors_keys = set()

    # ancestorsLevels L3 段: a1l3=l3 的 row (含 a1l4 不空)
    for k, rows in idx.items():
        for tno, pol, it in rows:
            if (it.get('a1_l1','') == l1 and it.get('a1_l2','') == l2 and
                it.get('a1_l3','') == l3):
                ancestors_keys.add((tno, pol, it.get('food',''), it.get('limit_value',''), it.get('sub_value','')))

    # ancestorsLevels L2 段: a1l2=l2, a1l3='', a1l4='' 的 row
    for k, rows in idx.items():
        for tno, pol, it in rows:
            if (it.get('a1_l1','') == l1 and it.get('a1_l2','') == l2 and
                not it.get('a1_l3','') and not it.get('a1_l4','')):
                ancestors_keys.add((tno, pol, it.get('food',''), it.get('limit_value',''), it.get('sub_value','')))

    # ancestorsLevels L1 段: a1l1=l1, a1l2='', a1l3='', a1l4='' 的 row
    for k, rows in idx.items():
        for tno, pol, it in rows:
            if (it.get('a1_l1','') == l1 and not it.get('a1_l2','') and
                not it.get('a1_l3','') and not it.get('a1_l4','')):
                ancestors_keys.add((tno, pol, it.get('food',''), it.get('limit_value',''), it.get('sub_value','')))

    # v82-fix83 跨 L2 段: a1l1=l1, a1l2!=l2, a1l3='', a1l4='' 的 row
    for k, rows in idx.items():
        for tno, pol, it in rows:
            if (it.get('a1_l1','') == l1 and it.get('a1_l2','') != l2 and it.get('a1_l2','') and
                not it.get('a1_l3','') and not it.get('a1_l4','')):
                ancestors_keys.add((tno, pol, it.get('food',''), it.get('limit_value',''), it.get('sub_value','')))

    # v82-fix84 跨 L4 兄弟: a1l1=l1, a1l2=l2, a1l3=l3, a1l4!=l4, a1l4!='' 的 row
    cross_l4_rows = []
    for k, rows in idx.items():
        for tno, pol, it in rows:
            if (it.get('a1_l1','') == l1 and it.get('a1_l2','') == l2 and
                it.get('a1_l3','') == l3 and it.get('a1_l4','') and it.get('a1_l4','') != l4):
                key = (tno, pol, it.get('food',''), it.get('limit_value',''), it.get('sub_value',''))
                if key in ancestors_keys:
                    continue
                cross_l4_rows.append((tno, pol, it))

    if cross_l4_rows:
        total_cross += len(cross_l4_rows)
        print(f'\n[L4] {l4[:40]} ({l1[:10]} / {l2[:15]} / {l3[:15]})')
        print(f'  跨 L4 兄弟 row ({len(cross_l4_rows)} 条):')
        for tno, pol, it in cross_l4_rows:
            lv = it.get('limit_value','')
            sv = it.get('sub_value','')
            food = it.get('food','')
            modif = it.get('modif','')
            a4 = it.get('a1_l4','')
            print(f'    [{tno}{pol}] val={lv}{("/"+sv) if sv else ""} {food[:30]} (L4挂载: {a4})')
            if modif:
                print(f'         modif: {modif}')

print(f'\n\n=== 总计跨 L4 兄弟 row: {total_cross} 条 ===')
