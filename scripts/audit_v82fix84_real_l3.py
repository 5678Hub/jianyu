"""v82-fix84 真实 L3 跨 L2 模拟（验证 walkExact ancestorsLevels + v82-fix83 跨 L2 段）

模拟 ancestorsLevels 段渲染：
- L2 段: idx.get('L1|L2')  -- 同 L2 通类 row
- L3 段: idx.get('L1|L2|L3') -- 同 L3 通类 row
- L4 段: idx.get('L1|L2|L3|L4') -- 同 L4 通类 row
- L1 段: idx.get('L1') -- L1 通类 row

v82-fix83 跨 L2 段：
- a1l1=L1, a1l2!=L2, a1l3/l4='' 的 row
- 仅 L3 节点 ancestorsLevels 段使用

v82-fix84 跨 L4 段：
- a1l1=L1, a1l2=L2, a1l3=L3, a1l4!=L4, a1l4!='' 的 row
- 仅 L4 节点 ancestorsLevels 段使用

判断: idx 空 L3/L4 节点经过 v82-fix83/v82-fix84 后，own+ancestorsLevels+跨段应当显示完整 row。
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

# 注册 idx
idx = {}
for con in d['contaminants']:
    for it in con['items']:
        parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
        pk = '|'.join([norm(p) for p in parts if p])
        if pk:
            idx.setdefault(pk, []).append((con['table_no'], con['contaminant'], it))

# 收集所有 L3/L4 节点
tree = d['appendix_a1']['tree']
all_nodes = []
def walk(node, path, depth):
    new_path = path + [node['name']]
    if depth >= 2:
        all_nodes.append(tuple(new_path))
    if depth >= 4:
        return
    for c in node.get('children', []):
        walk(c, new_path, depth + 1)

for n in tree:
    walk(n, [], 0)

# 模拟 walkExact ancestorsLevels + v82-fix83/84 跨段
def simulate_display(path):
    """模拟 walkExact 显示。返回 (own段, ancestorsLevels 各段, 跨段, L1段) row 数"""
    pk = '|'.join(norm(p) for p in path)

    own = idx.get(pk, [])

    ancestors = []
    # ancestorsLevels L2..L4 段
    for i in range(len(path) - 1, 0, -1):
        np = '|'.join(norm(p) for p in path[:i])
        ancestors.append((tuple(path[:i]), idx.get(np, [])))

    # v82-fix83 跨 L2 段 (仅 L3 节点)
    cross_l2 = []
    if len(path) == 3:
        l1, l2 = path[0], path[1]
        # 跨 L2 通类 row: a1l1=l1, a1l2!=l2, a1l3/l4=''
        for k, rows in idx.items():
            for tno, pol, it in rows:
                if (norm(it.get('a1_l1','')) == norm(l1) and
                    it.get('a1_l2','') and norm(it.get('a1_l2','')) != norm(l2) and
                    not it.get('a1_l3','') and not it.get('a1_l4','')):
                    cross_l2.append((tno, pol, it))

    # v82-fix84 跨 L4 段 (仅 L4 节点)
    cross_l4 = []
    if len(path) == 4:
        l1, l2, l3 = path[0], path[1], path[2]
        # 跨 L4 兄弟 row: a1l1=l1, a1l2=l2, a1l3=l3, a1l4!=path.l4, a1l4!=''
        for k, rows in idx.items():
            for tno, pol, it in rows:
                if (norm(it.get('a1_l1','')) == norm(l1) and
                    norm(it.get('a1_l2','')) == norm(l2) and
                    norm(it.get('a1_l3','')) == norm(l3) and
                    it.get('a1_l4','') and norm(it.get('a1_l4','')) != norm(path[3])):
                    cross_l4.append((tno, pol, it))

    return own, ancestors, cross_l2, cross_l4

# 主扫描
empty_l3 = []
empty_l4 = []
for path in all_nodes:
    pk = '|'.join(norm(p) for p in path)
    if not idx.get(pk):
        if len(path) == 3:
            empty_l3.append(path)
        elif len(path) == 4:
            empty_l4.append(path)

print(f'L3 idx 空: {len(empty_l3)} 个')
print(f'L4 idx 空: {len(empty_l4)} 个')
print()

# 检查 L3 idx 空节点 ancestorsLevels + v82-fix83 跨 L2 段合计显示 row
print('=== L3 idx 空节点 (own 0 行, ancestorsLevels + 跨 L2 段应有 row) ===')
print('--- 仅列仍有跨段 row=0 的节点 (fallback 链都为空) ---')
l3_total_row = 0
for path in empty_l3:
    own, ancestors, cross_l2, cross_l4 = simulate_display(path)
    own_n = len(own)
    anc_n = sum(len(a[1]) for a in ancestors)
    cross_n = len(cross_l2)
    total = own_n + anc_n + cross_n
    l3_total_row += total
    if total == 0:
        print(f'  ⚠️ 完全空: L3 {path[2]} (L1: {path[0][:8]})')

print(f'\nL3 idx 空总显示 row: {l3_total_row}')

# 检查 L4 idx 空节点
print()
print('=== L4 idx 空节点 (own 0 行) ===')
l4_total_row = 0
for path in empty_l4:
    own, ancestors, cross_l2, cross_l4 = simulate_display(path)
    own_n = len(own)
    anc_n = sum(len(a[1]) for a in ancestors)
    cross_n = len(cross_l4)
    total = own_n + anc_n + cross_n
    l4_total_row += total
    name = path[3]
    parent = path[2]
    print(f'  L4 {name[:25]:<25} ({parent[:15]}): own={own_n} anc={anc_n} cross_l4={cross_n} = {total}')

print(f'\nL4 idx 空总显示 row: {l4_total_row}')
