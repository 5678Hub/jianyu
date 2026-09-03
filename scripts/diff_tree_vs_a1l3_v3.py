import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

tree = data['appendix_a1']['tree']

# 模拟：如果 Fallback B 改成"丢弃"，idx 中哪些 row 被丢
def norm(s):
    return (s or '').lower()

def find_l2(nodes, name):
    for n in nodes:
        if n['name'] == name: return n
        if n.get('children'):
            r = find_l2(n['children'], name)
            if r: return r
    return None

def has_child(l2_node, l3_name):
    if not l2_node: return False
    children = l2_node.get('children', [])
    children_names = [c['name'] for c in children]
    children_cores = [re.sub(r'[([{【（].*$', '', n).strip() for n in children_names]
    return l3_name in children_names or l3_name in children_cores

dropped_count = 0
kept_count = 0
by_l2 = {}
for c in data['contaminants']:
    for it in c.get('items', []):
        a1l1 = it.get('a1_l1', '')
        a1l2 = it.get('a1_l2', '')
        a1l3 = it.get('a1_l3', '')
        a1l4 = it.get('a1_l4', '')
        if not a1l3 and not a1l4:
            continue
        l3 = a1l4 or a1l3
        l2_node = find_l2(tree, a1l2)
        if not has_child(l2_node, l3):
            dropped_count += 1
            by_l2[a1l2] = by_l2.get(a1l2, 0) + 1
        else:
            kept_count += 1

print(f'如改 Fallback B 行为,将被丢弃的 row 数: {dropped_count}')
print(f'保留的 row 数: {kept_count}')
print()
print(f'按 L2 分组 (受影响 row 数 > 0):')
for l2, cnt in sorted(by_l2.items(), key=lambda x: -x[1]):
    print(f'  L2={l2}: 丢 {cnt} 条')