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

print('tree type:', type(tree).__name__)
print('tree keys (if dict):', list(tree.keys()) if isinstance(tree, dict) else 'N/A')
print('tree (first 800 chars):')
print(json.dumps(tree, ensure_ascii=False)[:800])

print('\n--- 第一层 children ---')
if isinstance(tree, dict):
    children = tree.get('children', [])
    print(f'根 children 数: {len(children)}')
    if children:
        c0 = children[0]
        print(f'第一个 child keys: {list(c0.keys())}')
        print(f'第一个 child: {json.dumps(c0, ensure_ascii=False)[:300]}')
elif isinstance(tree, list):
    print(f'tree 是 list, 长度 {len(tree)}')
    if tree:
        print(f'第一项 keys: {list(tree[0].keys()) if isinstance(tree[0], dict) else type(tree[0])}')
        print(f'第一项: {json.dumps(tree[0], ensure_ascii=False)[:300]}')

# 统计所有含 'cat' 或 'id' 的 key 名
def collect_keys(node, key_set, path=''):
    if isinstance(node, dict):
        for k, v in node.items():
            key_set.add(k)
            if k in ('children',) and isinstance(v, list):
                for c in v:
                    collect_keys(c, key_set)
collect = set()
collect_keys(tree, collect)
print('\n所有出现过的 key:', sorted(collect))
