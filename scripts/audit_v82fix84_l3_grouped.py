"""v82-fix84 完整核对报告 — 按章节分组列出 L3 idx 空节点"""
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

def simulate_display(path):
    pk = '|'.join(norm(p) for p in path)
    own = idx.get(pk, [])
    ancestors = []
    for i in range(len(path) - 1, 0, -1):
        np = '|'.join(norm(p) for p in path[:i])
        ancestors.append((tuple(path[:i]), idx.get(np, [])))
    cross_l2 = []
    if len(path) == 3:
        l1, l2 = path[0], path[1]
        for k, rows in idx.items():
            for tno, pol, it in rows:
                if (norm(it.get('a1_l1','')) == norm(l1) and
                    it.get('a1_l2','') and norm(it.get('a1_l2','')) != norm(l2) and
                    not it.get('a1_l3','') and not it.get('a1_l4','')):
                    cross_l2.append((tno, pol, it))
    cross_l4 = []
    if len(path) == 4:
        l1, l2, l3 = path[0], path[1], path[2]
        for k, rows in idx.items():
            for tno, pol, it in rows:
                if (norm(it.get('a1_l1','')) == norm(l1) and
                    norm(it.get('a1_l2','')) == norm(l2) and
                    norm(it.get('a1_l3','')) == norm(l3) and
                    it.get('a1_l4','') and norm(it.get('a1_l4','')) != norm(path[3])):
                    cross_l4.append((tno, pol, it))
    return own, ancestors, cross_l2, cross_l4

# 按 L1 分组
by_l1 = {}
for path in all_nodes:
    pk = '|'.join(norm(p) for p in path)
    if idx.get(pk): continue  # 只看 idx 空
    if len(path) != 3: continue  # 只看 L3
    l1 = path[0]
    by_l1.setdefault(l1, []).append(path)

for l1 in sorted(by_l1.keys()):
    paths = by_l1[l1]
    print(f'\n## {l1} ({len(paths)} 个 L3 idx 空)')
    for path in paths:
        own, ancestors, cross_l2, _ = simulate_display(path)
        own_n = len(own)
        anc_n = sum(len(a[1]) for a in ancestors)
        cross_n = len(cross_l2)
        total = own_n + anc_n + cross_n
        # 列出每个段包含的污染物
        anc_pol = {}
        for anc_path, anc_rows in ancestors:
            for tno, pol, it in anc_rows:
                anc_pol.setdefault(pol, []).append(f'{anc_path[-1]}/{it.get("limit_value","")}')
        cross_pol = {}
        for tno, pol, it in cross_l2:
            cross_pol.setdefault(pol, []).append(f'{it.get("a1_l2","")[:10]}/{it.get("limit_value","")}')

        print(f'  L3 {path[2][:30]:<30} own={own_n} anc={anc_n} cross={cross_n} = total {total}')
        if anc_pol:
            print(f'    ancestorsLevels: {", ".join(f"{k}({len(v)})" for k,v in anc_pol.items())}')
        if cross_pol:
            print(f'    跨L2段: {", ".join(f"{k}({len(v)})" for k,v in cross_pol.items())}')
