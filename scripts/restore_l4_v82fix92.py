#!/usr/bin/env python3
"""v82-fix92: 恢复 7 个 A.1 节点 + 对应的 row a1l4"""
import json
import subprocess
import shutil

DATA = 'data/gb2762/gb2762_2025.json'

# 用户确认保留的 7 个节点
RESTORE_PATHS = [
    # (L1, L2, L3, L4)
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', None, '熏、烧、烤肉类'),
    ('水产动物及其制品', '水产制品', None, '海蜇制品'),
    ('水产动物及其制品', '水产制品', None, '鱼类制品'),
    ('水产动物及其制品', '水产制品', None, '其他鱼类制品'),
    ('水产动物及其制品', '水产制品', None, '其他水产品'),
    ('其他类（除上述食品以外的食品）', '花粉', None, '松花粉'),
    ('其他类（除上述食品以外的食品）', '花粉', None, '油菜花粉'),
]

with open(DATA, encoding='utf-8') as f:
    data = json.load(f)

shutil.copy(DATA, DATA + '.bak.v82fix92_restore')

# 1. 恢复 A.1 树节点
tree = data['appendix_a1']['tree']

def find_or_create(nodes, name):
    for n in nodes:
        if n.get('name') == name:
            return n
    return None

# 先用 v82-fix91 之前的版本恢复（git show b0c00ad~1）
# 因为 b0c00ad 是 v82-fix91 提交 (82917f7 是当前最新)，所以 b0c00ad 之前 = b0c00ad~1
r = subprocess.run(['git','show','b0c00ad~1:data/gb2762/gb2762_2025.json'], capture_output=True, text=True, encoding='utf-8')
data_v82fix90 = json.loads(r.stdout)

# 从 v82-fix90 之前版本中获取被删节点的完整定义
def find_node_in(nodes, name):
    for n in nodes:
        if n.get('name') == name:
            return n
    return None

added = 0
for l1, l2, l3, l4 in RESTORE_PATHS:
    # 找 L4 节点的完整定义（从 v82-fix90 之前版本）
    old_tree = data_v82fix90['appendix_a1']['tree']
    n1_old = find_node_in(old_tree, l1)
    if not n1_old: continue
    n2_old = find_node_in(n1_old.get('children', []), l2)
    if not n2_old: continue
    n3_old = None
    if l3:
        n3_old = find_node_in(n2_old.get('children', []), l3)
    else:
        n3_old = n2_old
    if not n3_old: continue

    n4_old = None
    for c in n3_old.get('children', []):
        if c.get('name') == l4:
            n4_old = c
            break
    if not n4_old: continue

    # 在当前 A.1 树中找到对应位置并恢复
    n1_now = find_node_in(tree, l1)
    if not n1_now: continue
    n2_now = find_node_in(n1_now.get('children', []), l2)
    if not n2_now: continue
    n3_now = None
    if l3:
        n3_now = find_node_in(n2_now.get('children', []), l3)
    else:
        n3_now = n2_now
    if not n3_now: continue

    if 'children' not in n3_now:
        n3_now['children'] = []

    # 检查是否已存在
    if not any(c.get('name') == l4 for c in n3_now['children']):
        n3_now['children'].append(n4_old)
        added += 1
        print(f'[OK] 恢复 {l1}/{l2}/{l4}')

print(f'\nA.1 树恢复: {added} 个节点')

# 2. 恢复 row 的 a1l4 字段（v82-fix90 之前版本中的值）
restored = 0
for c_now in data['contaminants']:
    name = c_now.get('contaminant', '')
    for item_now in c_now.get('items', []):
        if item_now.get('a1_l4', ''):
            continue  # 已有 a1l4
        # 在 v82-fix90 之前版本中查找匹配的 row
        food = item_now.get('food', '')
        l1 = item_now.get('a1_l1', '')
        l2 = item_now.get('a1_l2', '')
        l3 = item_now.get('a1_l3', '')
        for c_old in data_v82fix90['contaminants']:
            if c_old.get('contaminant', '') != name:
                continue
            for item_old in c_old.get('items', []):
                if (item_old.get('food', '') == food
                    and item_old.get('a1_l1', '') == l1
                    and item_old.get('a1_l2', '') == l2
                    and item_old.get('a1_l3', '') == l3
                    and item_old.get('a1_l4', '') in [r[3] for r in RESTORE_PATHS]):
                    item_now['a1_l4'] = item_old['a1_l4']
                    restored += 1
                    print(f'  [{name}] {food} a1l4={item_old["a1_l4"]}')
                    break

print(f'\nrow a1l4 恢复: {restored} 条')

# 写回
with open(DATA, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('已保存')
