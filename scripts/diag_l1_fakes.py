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
tree = data['appendix_a1']['tree']

# 收集 L1 + 假节点
l1_nodes = []
fake_nodes = []

def walk(node, parent_path='', level=0):
    name = node.get('name', '')
    if level == 0:
        cur_path = ''
    else:
        cur_path = (parent_path + ':' if parent_path else '') + name
    if level == 1:
        l1_nodes.append({'name': name, 'catid': node.get('catid'), 'path': cur_path})
    if level > 0 and 'catid' not in node:
        fake_nodes.append({'name': name, 'path': cur_path, 'level': level, 'parent': parent_path})
    for child in node.get('children', []):
        walk(child, cur_path, level+1)

for n in tree:
    walk(n)

print('=' * 70)
print('所有 L1 节点 (level=1)')
print('=' * 70)
for n in sorted(l1_nodes, key=lambda x: x.get('catid') or 0):
    cid = n.get('catid', 'NO_CATID')
    flag = '⚠️ 无catid' if n.get('catid') is None else ''
    print(f'  catid={cid:>4}  name: {n["name"]}  {flag}')

print('\n' + '=' * 70)
print(f'11 个假节点 (无 catid 非根) - 按 parent 路径分组')
print('=' * 70)
for fk in fake_nodes:
    print(f'  L{fk["level"]} | name: {fk["name"]}  | parent: {fk["parent"]}')