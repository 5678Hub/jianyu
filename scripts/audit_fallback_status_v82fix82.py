"""v82-fix82 优化扫描：每个 idx 空节点 + ancestorsLevels fallback row 清单

对每个 idx 空节点，列出:
1. ancestorsLevels 段的 row (来自 L2/L1 通类) - 是否完整覆盖
2. 同 L1 章节中 food 字段包含节点关键词的 row - 是否可复制挂载
3. 建议: 走 fallback / 复制挂载 / PDF 核对
"""
import json, re

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

# 模拟 walkExact 注册
def check_match(node, tno, pol, it):
    item_l3 = norm(it.get('a1_l3',''))
    item_l4 = norm(it.get('a1_l4',''))
    item_food = norm(it.get('food',''))
    node_l3 = norm(node[2]) if len(node) >= 3 else ''
    node_l4 = norm(node[3]) if len(node) >= 4 else ''

    # L4 精确
    if node_l4 and item_l4:
        if node_l4 == item_l4:
            return True
        if item_l4.startswith(node_l4) or node_l4.startswith(item_l4):
            return True  # fallback A

    # L3 精确
    if node_l3 and item_l3:
        if node_l3 == item_l3:
            return True
        if item_l3.startswith(node_l3) or node_l3.startswith(item_l3):
            return True  # fallback A
        # v32 core
        if node_l3 and node_l3 in item_food:
            return True

    return False

# 找 idx 命中节点
hit_nodes = set()
for tno, pol, it in all_items:
    for node in all_l3l4_nodes:
        if check_match(node, tno, pol, it):
            hit_nodes.add(node)

# idx 空节点
empty_nodes = [n for n in all_l3l4_nodes if n not in hit_nodes]

print(f'=== 总 L3/L4 节点: {len(all_l3l4_nodes)} | idx 命中: {len(hit_nodes)} | idx 空: {len(empty_nodes)} ===\n')

# 列出 ancestors fallback row
def get_ancestor_fallback(node):
    """返回 node 的 ancestorsLevels 段 row 列表"""
    l1, l2 = node[0], node[1]
    fallback_rows = []

    # L2 通类 row (a1l2=l2, a1l3='', a1l4='')
    pk_l2 = path_key([l1, l2])
    fallback_rows.extend([('L2通类', tno, pol, it) for tno, pol, it in row_register.get(pk_l2, [])])

    # L1 通类 row (a1l1=l1, a1l2='', a1l3='', a1l4='')
    pk_l1 = path_key([l1])
    fallback_rows.extend([('L1通类', tno, pol, it) for tno, pol, it in row_register.get(pk_l1, [])])

    # L2 通类 row 也包括 a1l3=通类名, a1l4='' 之类
    # 例如「肉制品(内脏制品、血制品除外)」a1l3='肉制品(包括内脏制品、血制品)' 等等
    # walkExact 的 ancestorsLevels 段会显示所有 path 在 l1/l2 层级但不在 l3/l4 层的 row
    for tno, pol, it in all_items:
        item_l1 = norm(it.get('a1_l1',''))
        item_l2 = norm(it.get('a1_l2',''))
        item_l3 = norm(it.get('a1_l3',''))
        node_l1 = norm(l1)
        node_l2 = norm(l2)
        # 路径在 l1+l2 层级匹配
        if item_l1 == node_l1 and item_l2 == node_l2:
            # 跳过 l3/l4 精确匹配（这些是 own row 的来源）
            if not item_l3:
                # L2 通类
                key = ('L2通类', tno, pol, it)
                if key not in fallback_rows:
                    fallback_rows.append(key)

    return fallback_rows

# 列出每章节 idx 空节点 + fallback 情况
by_l1 = {}
for n in empty_nodes:
    by_l1.setdefault(n[0], []).append(n)

# 已处理的节点（之前 v82-fix82 任务3）
already_processed = {
    # 肉及肉制品 10 个（已确认走 fallback）
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
    # 谷物 5 个（已确认走 fallback）
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '其他小麦粉制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '发酵面制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '生干面制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '生湿面制品（例如：面条、饺子皮、馄饨皮、烧麦皮等）'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '面糊（例如：用于鱼和禽肉的拖面糊）、裹粉、煎炸粉'),
    # 水产 2 个（已确认走 fallback）
    ('水产动物及其制品', '鲜、冻水产动物', '软体动物', '其他软体动物'),
    ('水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'),
}

# 也包括已处理的（头足类/腹足类已复制挂载 own row）
# 但 walkExact 现在会把它们识别为 idx 命中（因为复制挂载已写 own row 到 L4 路径）
# 所以 walkExact 后这 2 个不会在 idx 空列表里

# 列出未处理的 idx 空节点
remaining = [n for n in empty_nodes if n not in already_processed]

print(f'=== 已处理: {len(already_processed)} 个 | 剩余 idx 空: {len(remaining)} 个 ===\n')

# 按 L1 分组
by_l1_remaining = {}
for n in remaining:
    by_l1_remaining.setdefault(n[0], []).append(n)

# 按 PDF row 数从少到多（优先处理 row 数少的 L1）
l1_order = sorted(by_l1_remaining.keys(), key=lambda l1: len(by_l1_remaining[l1]))

for l1 in l1_order:
    nodes = by_l1_remaining[l1]
    print(f'\n## {l1} ({len(nodes)} 个 idx 空节点)')
    for n in nodes:
        depth = len([x for x in n if x])
        marker = 'L3' if depth == 3 else 'L4'
        fb = get_ancestor_fallback(n)
        fb_count = len(fb)
        fb_summary = []
        for tag, tno, pol, it in fb:
            lv = it.get('limit_value','')
            sv = it.get('sub_value','')
            fb_summary.append(f'{pol}({tno})={lv}{"/"+sv if sv else ""}')
        fb_str = ' | '.join(fb_summary[:5]) + (f' ...等{fb_count}条' if fb_count > 5 else '')
        path_str = ' / '.join([x for x in n if x])
        print(f'  [{marker}] {n[2] if depth==3 else n[3]}')
        print(f'        路径: {path_str}')
        print(f'        ancestorsLevels 段: {fb_count} 条 fallback row → {fb_str[:120]}')
