"""v82-fix82 跨 L2 漏显示分析

检查每个 idx 空节点的「跨 L2 漏显示」情况：
- PDF 表中 a1l1 匹配该节点 L1 的 row 有多少条
- walkExact ancestorsLevels 段实际显示多少条
- 差额 = 漏显示的 row 数
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

# 按 norm 路径索引
row_register = {}
for tno, pol, it in all_items:
    parts = [it.get(f'a1_l{i}','') for i in [1,2,3,4]]
    pk = path_key(parts)
    if pk:
        row_register.setdefault(pk, []).append((tno, pol, it))

# 收集所有 L3/L4 节点
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

# 找 idx 命中节点
hit_nodes = set()
for tno, pol, it in all_items:
    for node in all_l3l4_nodes:
        if check_match(node, tno, pol, it):
            hit_nodes.add(node)

empty_nodes = [n for n in all_l3l4_nodes if n not in hit_nodes]

# 已处理
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
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '预肉制品', '调理肉制品（生肉添加调理料）'),
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

# 检查每个节点的「PDF 中 a1l1 匹配该节点 L1 的 row 数」vs「walkExact ancestorsLevels 段 row 数」
def get_l1_matched_rows(node):
    """a1l1 与该节点 L1 匹配的所有 row (排除 L1 通类)"""
    l1 = node[0]
    rows = []
    for tno, pol, it in all_items:
        item_l1 = norm(it.get('a1_l1',''))
        item_l2 = norm(it.get('a1_l2',''))
        item_l3 = norm(it.get('a1_l3',''))
        node_l1 = norm(l1)
        if item_l1 == node_l1:
            # 排除 L1 通类 row (a1l1 匹配, 但 a1l2/l3/l4 全空)
            if not item_l2 and not item_l3 and not it.get('a1_l4',''):
                continue
            rows.append((tno, pol, it))
    return rows

def get_ancestors_fb_rows(node):
    """walkExact ancestorsLevels 段会显示的 row"""
    l1, l2 = node[0], node[1]
    fb = []
    # L2 通类 row (a1l1=node.l1, a1l2=node.l2, a1l3/l4 空)
    pk_l2 = path_key([l1, l2])
    for tno, pol, it in row_register.get(pk_l2, []):
        fb.append((tno, pol, it))
    return fb

# 漏显示 = L1 匹配 row - walkExact ancestorsLevels row
miss_summary = []
for node in remaining:
    l1_matched = get_l1_matched_rows(node)
    fb = get_ancestors_fb_rows(node)
    fb_pk = set()
    for tno, pol, it in fb:
        fb_pk.add(path_key([it.get(f'a1_l{i}','') for i in [1,2,3,4]]))

    # 漏显示: L1 matched 但 not in fb
    miss = []
    for tno, pol, it in l1_matched:
        pk = path_key([it.get(f'a1_l{i}','') for i in [1,2,3,4]])
        if pk not in fb_pk:
            miss.append((tno, pol, it))

    if miss:
        miss_count = len(miss)
        depth = len([x for x in node if x])
        marker = 'L3' if depth == 3 else 'L4'
        miss_summary.append((miss_count, node, miss))

# 按漏显示数从多到少排序
miss_summary.sort(key=lambda x: -x[0])

print(f'=== 有跨 L2 漏显示的节点: {len(miss_summary)} 个 ===\n')
for miss_count, node, miss in miss_summary[:30]:
    depth = len([x for x in node if x])
    marker = 'L3' if depth == 3 else 'L4'
    name = node[2] if depth == 3 else node[3]
    print(f'[{marker}] {node[0][:20]} / {node[1][:20]} / {name[:30]}')
    print(f'       漏显示 {miss_count} 条 (a1l1 匹配但 walkExact 不显示):')
    for tno, pol, it in miss[:5]:
        lv = it.get('limit_value','')
        sv = it.get('sub_value','')
        item_l2 = it.get('a1_l2','')
        item_l3 = it.get('a1_l3','')
        item_l4 = it.get('a1_l4','')
        loc = f'L1={node[0][:8]}/L2={item_l2[:15]}/L3={item_l3[:15]}/L4={item_l4[:15]}'
        print(f'         [{tno}{pol}] {lv}{("/"+sv) if sv else ""} | {loc}')
    if len(miss) > 5:
        print(f'         ...等 {len(miss)-5} 条')
    print()
