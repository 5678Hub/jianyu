"""检查 A.1 树关键 L3 节点下是否有 L4 子节点"""
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

# 找 谷物树
tree = data['appendix_a1']['tree']
def find_path(nodes, name, path):
    for n in nodes:
        if n['name'] == name:
            return path + [n['name']]
        if n.get('children'):
            r = find_path(n['children'], name, path + [n['name']])
            if r: return r
    return None

# 找关键 L3 节点的 children
targets = [
    '小麦粉（包括食用麸皮）',
    '大米（粉）',
    '玉米粉、玉米糁（渣）',
    '糙米（包括色稻米）',
    '稻谷', '玉米', '小麦',
]
for tgt in targets:
    path = find_path(tree, tgt, [])
    if not path:
        print(f'❌ {tgt}: not found in tree')
        continue
    # 找到该节点
    def find_n(nodes, name):
        for n in nodes:
            if n['name'] == name: return n
            if n.get('children'):
                r = find_n(n['children'], name)
                if r: return r
        return None
    node = find_n(tree, tgt)
    children = node.get('children', []) if node else []
    print(f'{"✅" if not children else "❗"} {tgt} (path: {"/".join(path)}): {len(children)} L4 children')
    for c in children:
        print(f'    └─ {c["name"]}')