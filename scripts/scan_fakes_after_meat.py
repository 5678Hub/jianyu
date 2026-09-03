import re, json

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 解析 inlineData
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

# 扫描所有无 catid 的节点 (根"食品"除外), 按 L1 分组
fakes_by_l1 = {}

def walk(node, l1_name='', level=0, path_names=None):
    if path_names is None:
        path_names = []
    name = node.get('name', '')
    has_catid = 'catid' in node
    is_root = (level == 0)
    if not has_catid and not is_root:
        # 假节点
        fakes_by_l1.setdefault(l1_name, []).append({
            'name': name,
            'level': level,
            'path': ' > '.join(path_names + [name]),
            'children': len(node.get('children', []))
        })
    # 确定 L1
    if level == 0:
        new_l1 = name  # "食品"
    elif level == 1:
        new_l1 = name
    else:
        new_l1 = l1_name
    for child in node.get('children', []):
        walk(child, new_l1, level+1, path_names + [name])

walk(tree)

print('=' * 60)
print('剩余无 catid 假节点扫描 (根"食品"除外)')
print('=' * 60)
total = 0
for l1, fakes in fakes_by_l1.items():
    print(f'\n【L1】{l1}  ({len(fakes)} 个假节点)')
    for fk in fakes:
        print(f'  L{fk["level"]} | {fk["name"]}  | path: {fk["path"]}')
        total += 1
print(f'\n总计: {total} 个假节点')

# 同时验证 contaminants: 检查 a1_l4 是否引用了已删除的假节点名
deleted_names = {'畜禽肝脏', '畜禽肾脏', '畜禽内脏制品', '熏、烧、烤肉类'}
print('\n' + '=' * 60)
print('contaminants 引用已删除假节点名检查 (肉类)')
print('=' * 60)
bad = 0
for cont in data['contaminants']:
    for it in cont['items']:
        l4 = it.get('a1_l4', '')
        if l4 in deleted_names:
            print(f'  [BAD] contaminant={cont.get("name","")} food={it.get("food","")} a1_l4={l4}')
            bad += 1
print(f'contaminants 错配: {bad} 行')

# 验证 additives
print('\n' + '=' * 60)
print('additives 引用已删除假节点名检查 (肉类)')
print('=' * 60)
bad_add = 0
for a in data['additives']:
    for row in a.get('rows', []):
        p = row.get('path', '')
        for dn in deleted_names:
            if dn in p:
                print(f'  [BAD] additive={a.get("name","")} path={p}')
                bad_add += 1
                break
print(f'additives 错配: {bad_add} 行')
