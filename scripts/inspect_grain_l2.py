"""查 A.1 树「其他谷物制品」节点精确名"""
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
tree = data['appendix_a1']['tree']

def find_path(nodes, name, path):
    for n in nodes:
        if name in n['name']:
            print(f'  CANDIDATE: {n["name"]} path={path + [n["name"]]}')
        if n.get('children'):
            find_path(n['children'], name, path + [n['name']])
    return None

print('=== 谷物 L1 子节点 ===')
grain_l1 = None
for n in tree:
    if '谷物' in n['name']:
        grain_l1 = n
        break
if grain_l1:
    for c in grain_l1.get('children', []):
        print(f'  L2: {c["name"]}')
        for gc in c.get('children', []):
            print(f'    L3: {gc["name"]}')