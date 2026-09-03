import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

tree = data['appendix_a1']['tree']

# 列 tree (l2, l3) 名
def find_l2(nodes, name):
    for n in nodes:
        if n['name'] == name: return n
        if n.get('children'):
            r = find_l2(n['children'], name)
            if r: return r
    return None

# 找所有 a1_l1..l3 的 row，并检查 a1_l3 是否在 tree 中
missing = {}
for c in data['contaminants']:
    for it in c.get('items', []):
        a1l1 = it.get('a1_l1', '')
        a1l2 = it.get('a1_l2', '')
        a1l3 = it.get('a1_l3', '')
        a1l4 = it.get('a1_l4', '')
        if not a1l3 and not a1l4:
            continue  # L2 通类项不需要查 tree
        l3 = a1l4 or a1l3
        l2_node = find_l2(tree, a1l2)
        if not l2_node:
            # L2 不在 tree — skip
            continue
        children = l2_node.get('children', [])
        children_names = [c['name'] for c in children]
        children_cores = [re.sub(r'[([{【（].*$', '', n).strip() for n in children_names]
        # 检查 l3 是否在 children
        if l3 not in children_names and l3 not in children_cores:
            key = (a1l2, l3)
            if key not in missing:
                missing[key] = []
            missing[key].append((c['contaminant'], it.get('food','')[:30], it.get('limit_value')))

# 输出
for (l2, l3), items in sorted(missing.items()):
    print(f"\n[L2={l2}] [L3={l3}] 缺失 ({len(items)} row 被 Fallback B 推到 idx[L2]):")
    for c, food, limit in items[:5]:
        print(f"  {c} | {food} | {limit}")
    if len(items) > 5:
        print(f"  ... 还有 {len(items) - 5} 条")