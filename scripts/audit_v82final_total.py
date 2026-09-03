"""v82-final 完整状态报告 - 整体核对 96 个 idx 空节点的实际显示"""
import json, re

with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

def norm(s):
    if not s: return ''
    s = str(s)
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】+]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s

idx = {}
for con in d['contaminants']:
    for it in con['items']:
        parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
        pk = '|'.join([norm(p) for p in parts if p])
        if pk:
            idx.setdefault(pk, []).append((con['table_no'], con['contaminant'], it))

tree = d['appendix_a1']['tree']
all_nodes = []
def walk(node, path, depth):
    new_path = path + [node['name']]
    if depth >= 2:
        all_nodes.append(tuple(new_path))
    if depth >= 4: return
    for c in node.get('children', []):
        walk(c, new_path, depth + 1)
for n in tree:
    walk(n, [], 0)

# 模拟祖先 L2/L1 通类 row 显示 (按 v82-fix82 + v82-fix85)
def get_l2_l1_fallback(path):
    """path[0]=L1, path[1]=L2, path[2]=L3 (L4 可选)
    L2 段: idx(path[0]+path[1]) 但只取 L2 通类 row (a1l2=l2, a1l3/l4=空)
    L1 段: idx(path[0]) 但只取 L1 通类 row (a1l2='', a1l3/l4=空)

    L3+ 节点 path.length >= 3: L1 段被 v82-fix82 过滤
    L2 节点 path.length === 2: L1 段保留
    """
    out = {'l2_rows': [], 'l1_rows': []}
    l1n, l2n = norm(path[0]), norm(path[1])

    # L2 段
    pk2 = '|'.join(norm(p) for p in path[:2])
    if pk2 in idx:
        for tno, pol, it in idx[pk2]:
            if (norm(it.get('a1_l1','')) == l1n and
                norm(it.get('a1_l2','')) == l2n and
                not it.get('a1_l3','') and not it.get('a1_l4','')):
                out['l2_rows'].append((tno, pol, it))

    # L1 段
    pk1 = '|'.join(norm(p) for p in path[:1])
    if pk1 in idx:
        for tno, pol, it in idx[pk1]:
            if (norm(it.get('a1_l1','')) == l1n and
                not it.get('a1_l2','') and
                not it.get('a1_l3','') and not it.get('a1_l4','')):
                out['l1_rows'].append((tno, pol, it))

    return out

# 按章节分组统计 idx 空节点
print('=== v82-final 96 个 idx 空节点 完整状态 ===\n')
by_l1 = {}
for path in all_nodes:
    pk = '|'.join(norm(p) for p in path)
    if idx.get(pk): continue
    by_l1.setdefault(path[0], []).append(path)

total = 0
real_pdf = 0  # 真实 PDF 表达 = ancestorsLevels 有 row
empty_pdf = 0  # PDF 表达为空
for l1 in sorted(by_l1.keys()):
    paths = by_l1[l1]
    has_anc = 0
    no_anc = 0
    for path in paths:
        depth = len(path)
        fb = get_l2_l1_fallback(path)
        if depth >= 3:
            anc_total = len(fb['l2_rows'])  # L3+ 不显示 L1 通类
        else:
            anc_total = len(fb['l2_rows']) + len(fb['l1_rows'])
        if anc_total > 0:
            has_anc += 1
        else:
            no_anc += 1
    total += len(paths)
    real_pdf += has_anc
    empty_pdf += no_anc
    print(f'## {l1} ({len(paths)} 个 idx 空: {has_anc} 有显示 + {no_anc} 无显示)')

print()
print(f'=== 总计 ===')
print(f'  idx 空节点总数: {total}')
print(f'  ancestorsLevels 有显示 (符合 PDF 表达): {real_pdf}')
print(f'  ancestorsLevels 无显示 (PDF 表达即空): {empty_pdf}')

# 列出 ancestorsLevels 全空的 idx 空节点
print()
print('=== ancestorsLevels 全空的 idx 空节点 (PDF 表达即空) ===')
for l1 in sorted(by_l1.keys()):
    paths = by_l1[l1]
    empty_in_l1 = []
    for path in paths:
        depth = len(path)
        fb = get_l2_l1_fallback(path)
        if depth >= 3:
            anc_total = len(fb['l2_rows'])
        else:
            anc_total = len(fb['l2_rows']) + len(fb['l1_rows'])
        if anc_total == 0:
            empty_in_l1.append(path)
    if empty_in_l1:
        print(f'\n## {l1}')
        for path in empty_in_l1:
            depth = len(path)
            name = path[2] if depth == 3 else path[3]
            print(f'  L{depth} {name[:40]} ({" > ".join(path[:depth-1])})')
