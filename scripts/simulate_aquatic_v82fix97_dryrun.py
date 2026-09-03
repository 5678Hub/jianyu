"""v82-fix97 (DRY-RUN) 模拟水产动物及其制品章节理想挂载

按用户 2026-09-03 13:30 反馈:
- 疑点 1: L3 软体动物 Cd 2.0 (实际 3 条冗余 row) → 拆 4 份挂 L4 双壳贝类 + L4 腹足类 + L4 头足类 + L3 棘皮类
- 疑点 2: L4 肉食性鱼类（金枪鱼、金目鲷、枪鱼、鲨鱼）→ 各自 Hg/甲基汞 row 挂 L4 肉食性鱼类
- 疑点 4: L4 海蜇制品/鱼类制品/其他鱼类制品/其他水产品 → 对应污染物 row 直接挂到具体 L4 节点
"""
import json

JSON_FILE = 'data/gb2762/gb2762_2025.json'


def norm(s):
    s = s or ''
    s = s.replace(',，、;；', '').replace('()（[【】', '').replace('：:', '').replace(' ', '').replace('|', '||')
    return s


def path_key(path):
    return '|'.join([norm(p) for p in path])


def build_item_index(data):
    itemIndex = {}
    for ci, c in enumerate(data['contaminants']):
        for ri, row in enumerate(c['items']):
            a1Path = [row.get('a1_l1', ''), row.get('a1_l2', ''), row.get('a1_l3', ''), row.get('a1_l4', '')]
            a1Path = [p for p in a1Path if p]
            clean = []
            for p in a1Path:
                if not clean or p != clean[-1]:
                    clean.append(p)
            if not clean:
                continue
            pk = path_key(clean)
            pol = row.get('pollutant') or row.get('main_label') or c['contaminant']
            itemIndex.setdefault(pk, []).append({
                'table_no': c['table_no'],
                'pollutant': pol,
                'food': row['food'],
                'limit_value': row['limit_value'],
                'unit': row.get('unit', ''),
                'inspection_method': row.get('inspection_method', ''),
                'note': row.get('note', '') or row.get('remark', ''),
            })
    return itemIndex


def simulate_ideal(data):
    """模拟 v82-fix97 理想挂载后的 idx 索引（不写回）"""
    simulated_items = []
    for c in data['contaminants']:
        new_items = [dict(it) for it in c['items']]
        simulated_items.append({'table_no': c['table_no'], 'contaminant': c['contaminant'], 'items': new_items})

    # ========== 疑点 1: L3 软体动物 Cd 2.0 (3 条冗余) → 拆 4 挂 ==========
    # ri=56/57/58 是同一 row 重复 3 次
    # 改为:
    #   ri=56 改 a1_l4='双壳贝类'
    #   ri=57 改 a1_l4='腹足类'
    #   ri=58 改 a1_l4='头足类'
    #   再 append 一条 a1_l3='棘皮类' a1_l4=''
    for c in simulated_items:
        if c['table_no'] != 2:
            continue
        target_l4 = ['双壳贝类', '腹足类', '头足类']
        matched_indices = []
        for ri, row in enumerate(c['items']):
            if (row.get('food') == '双壳贝类、腹足类、头足类、棘皮类'
                    and row.get('a1_l1') == '水产动物及其制品'
                    and row.get('a1_l3') == '软体动物'
                    and row.get('a1_l4') == ''):
                matched_indices.append(ri)
        if len(matched_indices) >= 3:
            # 前 3 条分别挂 3 个 L4
            for idx, l4_name in zip(matched_indices[:3], target_l4):
                c['items'][idx]['a1_l4'] = l4_name
                c['items'][idx]['food'] = l4_name
            # 再 append 一条挂 L3 棘皮类
            new_row = dict(c['items'][matched_indices[0]])
            new_row['a1_l3'] = '棘皮类'
            new_row['a1_l4'] = ''
            new_row['food'] = '棘皮类'
            c['items'].append(new_row)

    # ========== 疑点 3 (补充): T1 Pb 双壳贝类 1.5 → 复制挂 L4 双壳贝类 ==========
    for c in simulated_items:
        if c['table_no'] != 1:
            continue
        for row in c['items'][:]:
            if (row.get('food') == '双壳贝类'
                    and row.get('a1_l1') == '水产动物及其制品'
                    and row.get('a1_l2') == '鲜、冻水产动物'
                    and row.get('a1_l3') == '软体动物'
                    and row.get('a1_l4') == ''):
                # 复制挂 L4 双壳贝类
                new_row = dict(row)
                new_row['a1_l4'] = '双壳贝类'
                c['items'].append(new_row)

    # ========== 疑点 2: L4 肉食性鱼类挂 Hg/甲基汞 ==========
    # 金枪鱼/金目鲷/枪鱼/鲨鱼 各自的 Hg/甲基汞 row 移挂 L4 肉食性鱼类
    # 通类「肉食性鱼类及其制品」保持 L3 鱼类
    predator_names = ['金枪鱼', '金目鲷', '枪鱼', '鲨鱼']
    for c in simulated_items:
        if c['table_no'] != 3:
            continue
        for row in c['items'][:]:
            food = row.get('food', '')
            # 排除通类「肉食性鱼类及其制品」
            if '肉食性鱼类及其制品' in food:
                continue
            for name in predator_names:
                if food == f'{name}及其制品' and row.get('a1_l1') == '水产动物及其制品':
                    row['a1_l2'] = '鲜、冻水产动物'
                    row['a1_l3'] = '鱼类'
                    row['a1_l4'] = '肉食性鱼类（例如：金枪鱼、金目鲷、枪鱼、鲨鱼等）'
                    break

    # ========== 疑点 4: L3 海蜇制品/鱼类制品/其他鱼类制品/其他水产品 ==========
    # (注: A.1 树中这些是 L3 节点不是 L4, 现状已通过 walkExact Fallback B 正确挂载, 不需修改)
    # T1 Pb 海蜇制品 a1_l4='海蜇制品' → Fallback B → L3 海蜇制品 ✓
    # T1 Pb 鱼类制品 a1_l4='鱼类制品' → Fallback B → L3 鱼类制品 ✓
    # T2 Cd 其他鱼类制品 a1_l4='其他鱼类制品' → Fallback B → L3 其他鱼类制品 ✓
    # T10 NDMA 干制水产品 a1_l4='其他水产品' → Fallback B → L3 其他水产品 ✓
    # 这部分是 v82-fix92 恢复的结果, 保持现状

    new_data = {'contaminants': simulated_items}
    return build_item_index(new_data)


# 加载原始数据
with open(JSON_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

current_idx = build_item_index(data)
ideal_idx = simulate_ideal(data)

# 水产动物及其制品完整树
tree = data['appendix_a1']['tree']
all_paths = []


def walk(node, path):
    all_paths.append(path[:])
    for c in node.get('children', []):
        walk(c, path + [c['name']])


for item in tree:
    if item.get('name') == '水产动物及其制品':
        walk(item, ['水产动物及其制品'])
        break


def render_table(idx_map, label):
    print(f'\n=== {label} ===')
    print()
    for p in all_paths:
        pk = path_key(p)
        items = idx_map.get(pk, [])
        level = len(p)
        indent = '  ' * (level - 1)
        bar = '=' * (6 - level)
        print(f'{indent}{bar} L{level} {p[-1]} {bar}')
        if items:
            for it in items:
                note = ''
                if it['note']:
                    note = f" note={it['note']!r}"
                print(f'{indent}    T{it["table_no"]:>2} {it["pollutant"]} {it["food"]} {it["limit_value"]} {it["unit"]}{note}')
        else:
            print(f'{indent}    (空)')
        print()


render_table(current_idx, '现状（v82-fix96）')
render_table(ideal_idx, '理想挂载（v82-fix97 模拟）')
