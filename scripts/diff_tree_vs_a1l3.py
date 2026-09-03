import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

tree = data['appendix_a1']['tree']

# 列出 tree 所有 (a1_l2, a1_l3) 节点
def walk(nodes, parents):
    out = []
    for n in nodes:
        p = parents + [n['name']]
        out.append(tuple(p))
        if n.get('children'):
            out.extend(walk(n['children'], p))
    return out

tree_paths = walk(tree, [])
print(f"Tree 总节点数: {len(tree_paths)}")

# 列出 inlineData 所有 a1_l1..l4 路径
data_paths = set()
data_paths_by_l3 = {}  # (a1_l2, a1_l3) -> count
for c in data['contaminants']:
    for it in c.get('items', []):
        a1 = tuple([it.get(f'a1_l{i}', '') for i in range(1, 5) if it.get(f'a1_l{i}', '')])
        if len(a1) >= 3:
            data_paths_by_l3[(a1[1], a1[2])] = data_paths_by_l3.get((a1[1], a1[2]), 0) + 1

# 比较
print(f"\nInlineData 中出现的 (a1_l2, a1_l3) 但 tree 中没有 a1_l3 的:")
for (l2, l3), count in sorted(data_paths_by_l3.items()):
    # 找 l2 在 tree 的 children 列表
    l2_node = None
    for n in tree:
        if n['name'] == l2:
            l2_node = n; break
        if n.get('children'):
            for c in n['children']:
                if c['name'] == l2:
                    l2_node = c; break
    if not l2_node: continue
    children_names = [c['name'] for c in l2_node.get('children', [])]
    children_cores = [re.sub(r'[([{【（].*$', '', c).strip() for c in children_names]
    if l3 not in children_names and l3 not in children_cores:
        print(f"  L2={l2}, L3={l3}: 出现 {count} 次, 但 tree 中没有 '{l3}' 节点 (children: {children_names})")