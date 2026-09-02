"""v82-fix82 精确分析：跨 L2 漏显示的 L2 通类 row（不包括 L3/L4 own row）

逻辑：
- idx 空 L3 节点的 ancestorsLevels 应显示：所有 a1l1 = 节点 L1 的 L2 通类 row
- walkExact 当前只显示：a1l2 = 节点 L2 的 row
- 漏显示 = (a1l1 = 节点 L1) AND (a1l2 ≠ 节点 L2) AND (a1l3 = a1l4 = '') [即 L2 通类 row]
- 不算 L3/L4 own row（a1l3 或 a1l4 不空的）
"""
import json, re

with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

tree = d['appendix_a1']['tree']

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

row_register = {}
for tno, pol, it in all_items:
    parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
    pk = path_key(parts)
    if pk:
        row_register.setdefault(pk, []).append((tno, pol, it))

all_l3l4_nodes = []
def walk(node, path):
    new_path = path + [node['name']]
    if len(new_path) == 3:
        all_l3l4_nodes.append(tuple(new_path))
    elif len(new_path) == 4:
        all_l3l4_nodes.append(tuple(new_path))
    if len(new_path) < 4:
        for c in node.get('children', []):
            walk(c, new_path)

for n in tree:
    walk(n, [])

def check_match(node, tno, pol, it):
    item_l3 = norm(it.get('a1_l3',''))
    item_l4 = norm(it.get('a1_l4',''))
    item_food = norm(it.get('food',''))
    node_l3 = norm(node[2]) if len(node) >= 3 else ''
    node_l4 = norm(node[3]) if len(node) >= 4 else ''
    if node_l4 and item_l4:
        if node_l4 == item_l4: return True
        if item_l4.startswith(node_l4) or node_l4.startswith(item_l4): return True
    if node_l3 and item_l3:
        if node_l3 == item_l3: return True
        if item_l3.startswith(node_l3) or node_l3.startswith(item_l3): return True
        if node_l3 and node_l3 in item_food: return True
    return False

hit_nodes = set()
for tno, pol, it in all_items:
    for node in all_l3l4_nodes:
        if check_match(node, tno, pol, it):
            hit_nodes.add(node)

empty_nodes = [n for n in all_l3l4_nodes if n not in hit_nodes]

already_processed = {
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '其他熟肉制品'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '发酵肉制品类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '油炸肉类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '熟肉干制品（例如:肉干、肉松等）'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '肉灌肠类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '肉类罐头'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '西式火腿（熏烤、烟熏、蒸煮火腿）类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '酱卤肉制品类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '预制肉制品', '腌腊肉制品类（例如：咸肉、腊肉、板鸭、中式火腿、腊肠等）'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '预制肉制品', '调理肉制品（生肉添加调理料）'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '其他小麦粉制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '发酵面制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '生干面制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '生湿面制品（例如：面条、饺子皮、馄饨皮、烧麦皮等）'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '面糊（例如：用于鱼和禽肉的拖面糊）、裹粉、煎炸粉'),
    ('水产动物及其制品', '鲜、冻水产动物', '软体动物', '其他软体动物'),
    ('水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'),
}

remaining = [n for n in empty_nodes if n not in already_processed]
print(f'=== 剩余 idx 空: {len(remaining)} 个 ===\n')

# 精确分析：每个节点的「跨 L2 漏显示 L2 通类 row」
def get_cross_l2_miss(node):
    """a1l1 = 节点 L1, a1l2 ≠ 节点 L2, a1l3/l4 = 空 的 row (L2 通类, 应显示但 walkExact 不显示)"""
    l1, l2 = node[0], node[1]
    miss = []
    for tno, pol, it in all_items:
        item_l1 = norm(it.get('a1_l1',''))
        item_l2 = norm(it.get('a1_l2',''))
        item_l3 = it.get('a1_l3','')
        item_l4 = it.get('a1_l4','')
        node_l1 = norm(l1)
        node_l2 = norm(l2)

        # 必须是 a1l1 匹配该节点 L1
        if item_l1 != node_l1:
            continue
        # 必须是 L2 通类 row (a1l3/l4 全空)
        if item_l3 or item_l4:
            continue
        # 必须是 a1l2 ≠ 节点 L2 (跨 L2)
        if item_l2 == node_l2:
            continue
        # 必须 a1l2 不空
        if not item_l2:
            continue

        miss.append((tno, pol, it, item_l2))

    return miss

# 收集有跨 L2 漏显示的节点
nodes_with_miss = []
for node in remaining:
    miss = get_cross_l2_miss(node)
    if miss:
        nodes_with_miss.append((len(miss), node, miss))

nodes_with_miss.sort(key=lambda x: -x[0])
print(f'=== 有跨 L2 漏显示 L2 通类 row 的节点: {len(nodes_with_miss)} 个 ===\n')

# 按 L1 分组
by_l1 = {}
for cnt, node, miss in nodes_with_miss:
    by_l1.setdefault(node[0], []).append((cnt, node, miss))

for l1 in sorted(by_l1.keys()):
    items = by_l1[l1]
    print(f'\n## {l1} ({len(items)} 个)')
    for cnt, node, miss in items:
        depth = len([x for x in node if x])
        marker = 'L3' if depth == 3 else 'L4'
        name = node[2] if depth == 3 else node[3]
        print(f'  [{marker}] {name} | 漏显示 {cnt} 条 L2 通类 row')
        # 列所有漏显示 row
        for tno, pol, it, item_l2 in miss:
            lv = it.get('limit_value','')
            sv = it.get('sub_value','')
            print(f'      [{tno}{pol}] val={lv}{("/"+sv) if sv else ""} 来自 L2={item_l2[:25]}')
