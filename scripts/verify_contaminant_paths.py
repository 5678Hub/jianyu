import re, json

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
tree = data['appendix_a1']

# 建立 tree 路径集合: 每个有 catid 的节点的完整 name 链
# 同时建立 name->catid 映射 (按层级路径, 避免同名冲突)
tree_paths = set()  # "L1:L2:L3:L4" (空级跳过)
name_to_catid = {}  # path -> catid

def build_paths(node, parent_path='', level=0):
    name = node.get('name', '')
    if level == 0:
        # 根"食品", 不计入路径
        cur_path = ''
    else:
        cur_path = parent_path + (':' if parent_path else '') + name
    if 'catid' in node and level > 0:
        tree_paths.add(cur_path)
        name_to_catid[cur_path] = node['catid']
    for child in node.get('children', []):
        build_paths(child, cur_path, level+1)

build_paths(tree)

print(f'tree 有 catid 节点路径数: {len(tree_paths)}')

# 遍历 contaminants items, 检查 a1_l 路径
print('\n' + '=' * 70)
print('contaminants a1_l 路径在 tree 中查找结果')
print('=' * 70)

bad_items = []
seen_bad = set()  # 去重
for cont in data['contaminants']:
    cont_name = cont.get('name', '')
    for it in cont['items']:
        l1 = it.get('a1_l1', '')
        l2 = it.get('a1_l2', '')
        l3 = it.get('a1_l3', '')
        l4 = it.get('a1_l4', '')
        parts = [p for p in [l1, l2, l3, l4] if p]
        path = ':'.join(parts)
        # 检查各级前缀是否在 tree
        # 先检查完整 path
        if path in tree_paths:
            continue  # 完全匹配, OK
        # 检查各级前缀 (因为可能 l4 是空, 但 l3 在 tree)
        # 实际上 contaminants 的 a1_l 应该指向 tree 的叶子或中间节点
        # 如果 path 不在 tree_paths, 列出
        key = (path,)
        if key in seen_bad:
            continue
        seen_bad.add(key)
        bad_items.append({
            'cont': cont_name,
            'food': it.get('food', ''),
            'l1': l1, 'l2': l2, 'l3': l3, 'l4': l4,
            'path': path,
            'limit': it.get('limit', ''),
            'unit': it.get('unit', '')
        })

# 按 L1 分组输出
by_l1 = {}
for b in bad_items:
    by_l1.setdefault(b['l1'], []).append(b)

print(f'\n未在 tree 找到对应 catid 的 contaminants 路径: {len(bad_items)} 个 (去重)')
print(f'涉及 L1 大类: {len(by_l1)} 个')

for l1, items in by_l1.items():
    print(f'\n【{l1}】({len(items)} 项)')
    for b in items:
        l4_show = f' / L4={b["l4"]}' if b["l4"] else ' / (L4空)'
        l3_show = f'L3={b["l3"]}' if b["l3"] else '(L3空)'
        print(f'  {b["cont"]} | food={b["food"]} | {l3_show}{l4_show} | limit={b["limit"]}{b["unit"]}')
        print(f'    path: {b["path"]}')
