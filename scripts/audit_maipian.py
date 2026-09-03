"""查「麦片」L3 在 A.1 树 + 所有 row 中是否有"""
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

# 1) A.1 树中找「麦片」节点
tree = data['appendix_a1']['tree']
def find_path(nodes, name, path):
    for n in nodes:
        if n['name'] == name:
            return path + [n['name']]
        if n.get('children'):
            r = find_path(n['children'], name, path + [n['name']])
            if r: return r
    return None
def find_n(nodes, name):
    for n in nodes:
        if n['name'] == name: return n
        if n.get('children'):
            r = find_n(n['children'], name)
            if r: return r
    return None

mp = find_path(tree, '麦片', [])
print(f'A.1 树 麦片 节点: {mp}')
mp_node = find_n(tree, '麦片')
print(f'A.1 树 麦片 子节点数: {len(mp_node.get("children", [])) if mp_node else "N/A"}')

# 2) 查所有 row 中 food 含「麦片」
print('\n所有污染物 row 中含「麦片」:')
for t in data['contaminants']:
    sym = t.get('symbol', '')
    for idx, it in enumerate(t['items']):
        food = it.get('food', '')
        if '麦片' in food:
            print(f'  [{sym}] idx={idx} a1l1={it.get("a1_l1","")[:20]} a1l2={it.get("a1_l2","")[:20]} a1l3={it.get("a1_l3","")[:20]} a1l4="{it.get("a1_l4","")}" food={food} limit={it.get("limit_value","") or it.get("limit","")}')