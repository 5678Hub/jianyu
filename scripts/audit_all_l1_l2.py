"""扫描所有 L1 + L2 节点的 own row 归属"""
import re, json
with open(r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'<script type="application/json" id="inlineData">', c)
s = m.end()
depth = 0; in_str = False; esc = False; i = s
while i < len(c):
    ch = c[i]
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
    else:
        if ch == '"': in_str = True
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: e = i + 1; break
    i += 1
data = json.loads(c[s:e])

# 1) 列出 A.1 树所有 L1 + L2 节点
tree = data['appendix_a1']['tree']
def walk(nodes, depth, path):
    for n in nodes:
        cur_path = path + [n['name']]
        yield (depth, cur_path, n.get('children', []))
        if n.get('children'):
            yield from walk(n['children'], depth+1, cur_path)

l1_paths = []
l2_paths = []
for d, p, ch in walk(tree, 1, []):
    if d == 1:
        l1_paths.append(p)
    elif d == 2:
        l2_paths.append(p)
    elif d == 3:
        pass  # L3 已扫

# 2) 对每个 L1 + L2 节点，统计 own row
def own_rows_for_l1l2(l1_path, l2_path=None):
    matches = []
    for t in data['contaminants']:
        sym = t.get('symbol', '')
        for idx, it in enumerate(t['items']):
            if it.get('a1_l1') != l1_path[0]:
                continue
            if l2_path is None:
                # L1 own row: a1_l2 空
                if not it.get('a1_l2'):
                    matches.append((sym, idx, it))
            else:
                # L2 own row: a1_l2 = l2_path[1], a1_l3 空
                if it.get('a1_l2') == l2_path[1] and not it.get('a1_l3'):
                    matches.append((sym, idx, it))
    return matches

# 输出 L1 节点的 own row
print('=' * 100)
print('L1 节点 own row 扫描')
print('=' * 100)
for p in l1_paths:
    rows = own_rows_for_l1l2(p)
    if rows:
        print(f'\n【{p[0]}】')
        for sym, idx, it in rows:
            food = it.get('food', '')
            limit = it.get('limit_value', '') or it.get('limit', '') or it.get('main_limit', '')
            sub = it.get('sub_value', '')
            print(f'  [{sym}] idx={idx} food={food[:40]} lim={limit}{("/"+sub) if sub else ""}')

print('\n' + '=' * 100)
print('L2 节点 own row 扫描')
print('=' * 100)
for p in l2_paths:
    rows = own_rows_for_l1l2(p[0], p)
    if rows:
        print(f'\n【{p[0]} > {p[1]}】')
        for sym, idx, it in rows:
            food = it.get('food', '')
            limit = it.get('limit_value', '') or it.get('limit', '') or it.get('main_limit', '')
            sub = it.get('sub_value', '')
            print(f'  [{sym}] idx={idx} food={food[:40]} lim={limit}{("/"+sub) if sub else ""}')

# 3) 检查哪些 L2 节点没有 own row（依赖 ancestorsLevels）
print('\n' + '=' * 100)
print('L2 节点无 own row 列表（依赖 ancestorsLevels fall back）')
print('=' * 100)
for p in l2_paths:
    rows = own_rows_for_l1l2(p[0], p)
    if not rows:
        print(f'  {p[0]} > {p[1]}')