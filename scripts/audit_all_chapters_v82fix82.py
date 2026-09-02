"""v82-fix82 全章节扫描：所有 L3/L4 节点 + idx 空节点清单

完整 walkExact 模拟，包含 norm() + fallback A/B + v32 core 匹配
"""
import json, re, sys

with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

tree = d['appendix_a1']['tree']

# 收集所有 items
all_items = []
for con in d['contaminants']:
    for it in con['items']:
        all_items.append((con['table_no'], con['contaminant'], it))

def norm(s):
    if not s:
        return ''
    s = s.replace('（','(').replace('）',')')
    s = re.sub(r'[\s,，、。\.]','', s)
    s = re.sub(r'\([^)]*\)', '', s)
    return s

def path_key(parts):
    return '|'.join([norm(p) for p in parts if p])

# 按 norm 路径索引
row_register = {}  # path_key -> [(tno, pol, it)]
for tno, pol, it in all_items:
    parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
    pk = path_key(parts)
    if pk:
        row_register.setdefault(pk, []).append((tno, pol, it))

# 收集所有 L3/L4 节点
all_l3l4_nodes = []  # [(l1, l2, l3, l4)]

def walk(node, path):
    new_path = path + [node['name']]
    # tree 是 L1 节点列表 (排除 食品 root), 所以:
    # len(new_path) == 1 → L1, 2 → L2, 3 → L3, 4 → L4
    if len(new_path) == 3:  # L3 节点
        all_l3l4_nodes.append(tuple(new_path))
    elif len(new_path) == 4:  # L4 节点
        all_l3l4_nodes.append(tuple(new_path))
    if len(new_path) < 4:
        for c in node.get('children', []):
            walk(c, new_path)

# 遍历 tree
for n in tree:
    walk(n, [])

print(f'=== 总 L3+L4 节点: {len(all_l3l4_nodes)} ===')

# 模拟 walkExact 注册逻辑（fallback A/B/v32 core）
# v32 core: 节点核心词 in row food 核心词 或反之
def match_item_to_node(pk_parts, tno, pol, it):
    """检查 item 是否会注册到 pk_parts 路径上"""
    item_l3 = norm(it.get('a1_l3',''))
    item_l4 = norm(it.get('a1_l4',''))
    item_food = norm(it.get('food',''))

    # L4 注册 (精确匹配)
    if len(pk_parts) == 4 and item_l4:
        l4 = norm(pk_parts[3])
        if l4 == item_l4:
            return 'exact_l4'
        # fallback A: item_l4 是 l4 的前缀
        if item_l4.startswith(l4) or l4.startswith(item_l4):
            return 'fallback_a_l4'

    # L3 注册
    if len(pk_parts) >= 3 and item_l3:
        l3 = norm(pk_parts[2])
        if l3 == item_l3:
            return 'exact_l3'
        # fallback A: item_l3 是 l3 的前缀
        if item_l3.startswith(l3) or l3.startswith(item_l3):
            return 'fallback_a_l3'
        # v32 core: 节点核心词 in row food 核心词
        if l3 and l3 in item_food:
            return 'v32_core_match'

    return None

# 收集每个节点匹配到的 row
node_match = {}  # (l1, l2, l3, l4) -> [(tno, pol, it, match_type)]
for tno, pol, it in all_items:
    parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
    norm_parts = [norm(p) for p in parts if p]

    # 尝试匹配每个 L3/L4 节点
    for node in all_l3l4_nodes:
        node_parts = [norm(n) for n in node]
        # 检查 item 路径是否与 node 路径匹配（层级对齐）
        if len(norm_parts) > len(node_parts):
            continue

        # 检查前缀匹配
        matched = True
        for i, np in enumerate(norm_parts):
            if i >= len(node_parts):
                matched = False
                break
            if node_parts[i] != np:
                matched = False
                break

        if matched:
            # 注册到该 node
            mt = match_item_to_node(node, tno, pol, it)
            if mt:
                node_match.setdefault(node, []).append((tno, pol, it, mt))

# 统计 idx 空节点 (无任何 own row)
empty_nodes = []
for node in all_l3l4_nodes:
    matches = node_match.get(node, [])
    # 过滤掉 Fallback A（不算 own row 命中）
    own_matches = [m for m in matches if not m[3].startswith('fallback_a')]
    if not own_matches:
        empty_nodes.append(node)

print(f'\\n=== idx 空 L3/L4 节点: {len(empty_nodes)} 个 ===\\n')

# 按 L1 分组打印
by_l1 = {}
for n in empty_nodes:
    by_l1.setdefault(n[0], []).append(n)

for l1, nodes in by_l1.items():
    print(f'\\n## {l1} ({len(nodes)} 个)')
    for n in nodes:
        depth = len([x for x in n if x])
        marker = 'L3' if depth == 3 else 'L4'
        path_str = ' / '.join([x for x in n if x])
        print(f'  [{marker}] {path_str}')

# 额外：输出 idx 命中的节点数（有 own row）
hit_count = sum(1 for n in all_l3l4_nodes if n in node_match)
print(f'\\n=== idx 命中 L3/L4 节点: {hit_count} 个 ===')
print(f'=== 总 L3/L4 节点: {len(all_l3l4_nodes)} 个 ===')
