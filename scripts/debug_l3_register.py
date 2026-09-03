"""
Debug: 看 0.04 葡萄汁 的 walkExact 注册路径 + v23 sibling 扩散
"""
import json
import re

DATA = json.load(open('data/gb2762/gb2762_2025.json', encoding='utf-8'))
tree = DATA['appendix_a1']['tree']

def norm(s):
    if not s: return ''
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

# 找 L2 果蔬汁类及其饮料 节点
l2_node = None
for n in tree:
    if n['name'] == '饮料类':
        for c2 in n.get('children', []):
            if '果蔬汁类及其饮料' in c2['name']:
                l2_node = c2
                break

print('L2 节点:', l2_node['name'])
print('L2 children:')
for c in l2_node.get('children', []):
    print(f'  - {c["name"]!r} (norm={norm(c["name"])!r})')
print()

# 测试 row 0.04 葡萄汁
row = {'food': '葡萄汁', 'a1_l1': '饮料类',
       'a1_l2': '果蔬汁类及其饮料（例如：苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等）',
       'a1_l3': '果蔬汁（浆）', 'a1_l4': ''}

def walk_exact_simple(a1path, tree):
    if not a1path: return []
    matched_paths = []
    def _walk(nodes, path, idx):
        if idx >= len(a1path): return
        target = norm(a1path[idx])
        matched_here = False
        for n in nodes:
            nname = norm(n['name'])
            matched = (nname == target)
            if not matched and idx == len(a1path) - 1 and len(target) >= 3 and nname.startswith(target):
                matched = True
            if matched:
                matched_here = True
                cur_path = path + [n['name']]
                if idx < len(a1path) - 1 and n.get('children'):
                    _walk(n['children'], cur_path, idx + 1)
                else:
                    matched_paths.append(cur_path)
        if (not matched_here and idx == len(a1path) - 1
                and len(path) > 0):
            matched_paths.append(path[:])
    _walk(tree, [], 0)
    return matched_paths

ap = [row.get('a1_l1'), row.get('a1_l2'), row.get('a1_l3'), row.get('a1_l4')]
ap = [x for x in ap if x]
print(f'walkExact a1path={ap}')
matched_paths = walk_exact_simple(ap, tree)
print(f'  matched_paths:')
for p in matched_paths:
    print(f'    {p}')
print()

# v23 sibling expansion
print('=== v23 sibling detection ===')
food = row['food']
food_lc = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', food).lower()
for p in matched_paths:
    if len(p) < 3: continue
    start_path = p[:-1]
    cur = None
    for sp in start_path:
        children = cur['children'] if cur else tree
        f = next((c for c in children if c['name'] == sp), None)
        if not f: break
        cur = f
    if not cur or not cur.get('children'): continue
    print(f'  matched_path: {p}')
    print(f'  start_path: {start_path}')
    print(f'  food={food!r} food_lc={food_lc!r}')
    for sib in cur['children']:
        if sib['name'] == p[-1]:
            print(f'    sib={sib["name"]!r} [SKIP current]')
            continue
        sib_core = re.sub(r'[([{【（].*$', '', sib['name']).strip()
        sib_core_lc = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', sib_core).lower()
        c1 = bool(sib_core) and sib_core_lc in food_lc
        c2 = len(sib_core) >= 3 and sib['name'] in food
        match = c1 or c2
        marker = '✓ MATCH' if match else '✗'
        print(f'    sib={sib["name"]!r} core={sib_core!r} core_lc={sib_core_lc!r}')
        print(f'      c1={c1} (sib_core_lc in food_lc)')
        print(f'      c2={c2} (sib.name in food)')
        print(f'      → {marker}')
