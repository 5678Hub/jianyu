"""v82-fix85 后整体核对 - 列出 ancestorsLevels 段显示 0 条 row 的 idx 空节点"""
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

def simulate(path):
    pk = '|'.join(norm(p) for p in path)
    own = idx.get(pk, [])
    ancestors = []
    for i in range(len(path) - 1, 0, -1):
        np = '|'.join(norm(p) for p in path[:i])
        ancestors.append(idx.get(np, []))
    return own, ancestors

# 找 ancestorsLevels 段全空的 idx 空节点
print('=== v82-fix85 后 ancestorsLevels 段全空 (祖先全 idx 空) 的 idx 空节点 ===\n')
empty_anc = []
for path in all_nodes:
    pk = '|'.join(norm(p) for p in path)
    if idx.get(pk): continue  # idx 命中
    own, ancestors = simulate(path)
    anc_total = sum(len(a) for a in ancestors)
    if anc_total == 0:
        empty_anc.append(path)

print(f'共 {len(empty_anc)} 个节点 ancestorsLevels 段全空')
print()
by_l1 = {}
for p in empty_anc:
    by_l1.setdefault(p[0], []).append(p)
for l1 in sorted(by_l1.keys()):
    print(f'## {l1}')
    for path in by_l1[l1]:
        depth = len(path)
        name = path[2] if depth == 3 else (path[3] if depth == 4 else path[1])
        l2 = path[1]
        if depth == 4:
            l3 = path[2]
            l4 = path[3]
            print(f'  L4 {l4} ({l2} > {l3})')
        else:
            print(f'  L3 {name}')
    print()

# 列出 ancestorsLevels 段显示 1 条的节点（数量少可能需要补充）
print('\n=== ancestorsLevels 段只显示 1 条 row 的 idx 空节点 ===\n')
one_anc = []
for path in all_nodes:
    pk = '|'.join(norm(p) for p in path)
    if idx.get(pk): continue
    own, ancestors = simulate(path)
    anc_total = sum(len(a) for a in ancestors)
    if anc_total == 1:
        one_anc.append((path, ancestors))

for path, ancestors in one_anc:
    depth = len(path)
    name = path[2] if depth == 3 else path[3]
    print(f'  L{depth} {name[:35]} ({path[0][:15]} > {path[1][:15]}):')
    for a in ancestors:
        for tno, pol, it in a:
            print(f'    [{tno}{pol}] {it.get("food","")[:30]} val={it.get("limit_value","")}')
