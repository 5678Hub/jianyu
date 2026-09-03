import re, json, os
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script type="application/json" id="inlineData">', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg = html[seg_start:seg_start+m2.start()]

depth = 0; obj_end = -1; in_str = False; esc = False
for i, ch in enumerate(seg):
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
        continue
    if ch == '"': in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = i+1; break

data = json.loads(seg[:obj_end])

# 真实 tree 在 appendix_a1.tree
appendix = data['appendix_a1']
print('appendix_a1 keys:', list(appendix.keys()))
tree = appendix['tree']
print('tree type:', type(tree).__name__)
print('tree first item (前 300 字):', json.dumps(tree[0] if isinstance(tree, list) else tree, ensure_ascii=False)[:300])

# 建立 tree 路径 (用 catid 字段)
tree_paths = {}  # path -> catid
fake_nodes = []  # 无 catid 的非根节点

def walk(node, parent_path='', level=0):
    name = node.get('name', '')
    if level == 0:
        cur_path = ''
    else:
        cur_path = (parent_path + ':' if parent_path else '') + name
    if 'catid' in node and level > 0:
        tree_paths[cur_path] = node['catid']
    elif level > 0:
        fake_nodes.append({'name': name, 'path': cur_path, 'level': level})
    for child in node.get('children', []):
        walk(child, cur_path, level+1)

if isinstance(tree, list):
    for n in tree:
        walk(n)
else:
    walk(tree)

print(f'\ntree 有 catid 节点数: {len(tree_paths)}')
print(f'tree 假节点数 (无 catid 非根): {len(fake_nodes)}')

# 找 L1 = 谷物及其制品 的所有 catid 路径
# 兼容全角半角括号
l1_names = ['谷物及其制品（不包括焙烤制品）', '谷物及其制品(不包括焙烤制品)']
l1_catid = None
l1_path = None
for p, c in tree_paths.items():
    for ln in l1_names:
        if p == ln or p.startswith(ln + ':'):
            if l1_catid is None:
                l1_catid = c
                l1_path = ln
            break
print(f'\nL1 catid={l1_catid}, L1 name="{l1_path}"')

print('\n' + '=' * 70)
print(f'[L1 谷物及其制品] 下所有 catid 路径 (按 catid 排序)')
print('=' * 70)
grain_paths = {p: c for p, c in tree_paths.items() if p.startswith(l1_path + ':') or p == l1_path}
grain_paths_sorted = sorted(grain_paths.items(), key=lambda x: (x[1], x[0]))
for p, c in grain_paths_sorted:
    rel = p[len(l1_path):]
    print(f'  catid={c:3d}  {rel}')

# 提取 L1 = 谷物及其制品 下所有 contaminants row
print('\n' + '=' * 70)
print(f'contaminants 中 L1 = {l1_path} 的所有 row (完整 a1_l + food + limit)')
print('=' * 70)
from collections import defaultdict
by_cont = defaultdict(list)
for cont in data['contaminants']:
    cont_name = cont.get('name', '')
    for it in cont['items']:
        for ln in l1_names:
            if it.get('a1_l1') == ln:
                by_cont[cont_name].append({
                    'food': it.get('food', ''),
                    'l2': it.get('a1_l2', ''),
                    'l3': it.get('a1_l3', ''),
                    'l4': it.get('a1_l4', ''),
                    'limit': it.get('limit', ''),
                    'unit': it.get('unit', '')
                })
                break

for cont_name, items in sorted(by_cont.items()):
    print(f'\n【{cont_name}】({len(items)} 条)')
    for it in items:
        l2 = it['l2'] or '(L2空)'
        l3 = it['l3'] or '(L3空)'
        l4 = f'/L4={it["l4"]}' if it['l4'] else '/(L4空)'
        food = it['food'][:60] + ('...' if len(it['food']) > 60 else '')
        print(f'  L2={l2}  L3={l3}{l4}')
        print(f'    food: {food}  limit: {it["limit"]} {it["unit"]}')

# 重点: 找总汞行 (food 含"稻谷"+"玉米"+"小麦")
print('\n' + '=' * 70)
print('[焦点] 总汞这一行的完整数据 (food 含 稻谷/玉米/小麦)')
print('=' * 70)
for cont in data['contaminants']:
    if cont.get('name') != '总汞':
        continue
    for it in cont['items']:
        for ln in l1_names:
            if it.get('a1_l1') == ln:
                food = it.get('food', '')
                if '稻谷' in food and '玉米' in food and '小麦' in food:
                    print(f'\n  full record:')
                    print(f'    a1_l1: {it.get("a1_l1","")}')
                    print(f'    a1_l2: {it.get("a1_l2","")}')
                    print(f'    a1_l3: {it.get("a1_l3","")}')
                    print(f'    a1_l4: {it.get("a1_l4","")}')
                    print(f'    food: {food}')
                    print(f'    limit: {it.get("limit","")} {it.get("unit","")}')
                    # 拼路径, 检查各级
                    full = ':'.join([it.get(f'a1_l{i}','') for i in [1,2,3,4] if it.get(f'a1_l{i}','')])
                    print(f'    full path: "{full}"')
                    if full in tree_paths:
                        print(f'    ✓ 完整路径在 tree 找到 (catid={tree_paths[full]})')
                    else:
                        print(f'    ✗ 完整路径在 tree 找不到 (被 Fallback B 推到 L2 谷物)')
                    # 试各级前缀
                    for i in [4,3,2,1]:
                        parts = [it.get(f'a1_l{j}','') for j in [1,2,3,4] if it.get(f'a1_l{j}','')][:i]
                        p = ':'.join(parts)
                        if p in tree_paths:
                            print(f'    前 i={i} 级命中: "{p}" → catid={tree_paths[p]}')
