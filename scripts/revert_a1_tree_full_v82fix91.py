#!/usr/bin/env python3
"""v82-fix91: 撤回 v82-fix82 (136b4bd) 在 A.1 树中添加的所有错误节点"""
import json
import shutil

DATA = 'data/gb2762/gb2762_2025.json'

# v82-fix82 在 A.1 树中添加的所有节点（按章节路径）
ADDED_PATHS = [
    # 食用菌
    ('食用菌及其制品', '食用菌制品', '松茸制品'),
    ('食用菌及其制品', '食用菌制品', '松露制品'),
    ('食用菌及其制品', '食用菌制品', '牛肝菌制品'),
    ('食用菌及其制品', '食用菌制品', '鸡枞制品'),
    ('食用菌及其制品', '食用菌制品', '多汁乳菇制品'),
    ('食用菌及其制品', '食用菌制品', '羊肚菌制品'),
    ('食用菌及其制品', '食用菌制品', '獐头菌制品'),
    ('食用菌及其制品', '食用菌制品', '青头菌制品'),
    ('食用菌及其制品', '食用菌制品', '鸡油菌制品'),
    ('食用菌及其制品', '食用菌制品', '榛蘑制品'),
    ('食用菌及其制品', '食用菌制品', '姬松茸制品'),
    ('食用菌及其制品', '食用菌制品', '香菇制品'),
    ('食用菌及其制品', '食用菌制品', '木耳制品'),
    ('食用菌及其制品', '食用菌制品', '银耳制品'),
    # 坚果及籽类
    ('坚果及籽类', '生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）', '生咖啡豆及烘焙咖啡豆'),
    # 肉及肉制品
    ('肉及肉制品', '肉类（生鲜肉、冷却肉、冷冻肉等）', '畜禽肝脏'),
    ('肉及肉制品', '肉类（生鲜肉、冷却肉、冷冻肉等）', '畜禽肾脏'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '畜禽内脏制品'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熏、烧、烤肉类'),
    # 水产动物及其制品
    ('水产动物及其制品', '水产制品', '海蜇制品'),
    ('水产动物及其制品', '水产制品', '鱼类制品'),
    ('水产动物及其制品', '水产制品', '其他鱼类制品'),
    ('水产动物及其制品', '水产制品', '其他水产品'),
    # 油脂及其制品
    ('油脂及其制品', '动物油脂（例如：猪油、牛油、鱼油、磷虾油等）', '水产动物油脂'),
    # 调味品
    ('调味品', '其他调味品', '固态调味品'),
    # 酒类
    ('酒类', '蒸馏酒（例如：白酒、白兰地、威士忌、伏特加、朗姆酒等）', '白酒'),
    # 特殊膳食用食品
    ('特殊膳食用食品', '婴幼儿辅助食品', '以水产及动物肝脏为原料的产品'),
    ('特殊膳食用食品', '婴幼儿辅助食品', '添加藻类的产品'),
    # 其他类
    ('其他类（除上述食品以外的食品）', '花粉', '松花粉'),
    ('其他类（除上述食品以外的食品）', '花粉', '油菜花粉'),
]

with open(DATA, encoding='utf-8') as f:
    data = json.load(f)

# 备份
shutil.copy(DATA, DATA + '.bak.v82fix91_revert_full')

# 1. 撤回 A.1 树节点
tree = data['appendix_a1']['tree']

def find_in_tree(nodes, name):
    for n in nodes:
        if n.get('name') == name:
            return n
    return None

removed_count = 0
for l1, l2, l3 in ADDED_PATHS:
    n1 = find_in_tree(tree, l1)
    if not n1:
        print(f'[SKIP] 找不到 L1: {l1}')
        continue
    n2 = find_in_tree(n1.get('children', []), l2)
    if not n2:
        print(f'[SKIP] 找不到 L2: {l2} (在 {l1} 下)')
        continue
    before = len(n2.get('children', []))
    n2['children'] = [c for c in n2.get('children', []) if c.get('name') != l3]
    after = len(n2.get('children', []))
    if before > after:
        print(f'[OK] {l1}/{l2}: 移除 {l3}')
        removed_count += 1
    else:
        print(f'[SKIP] {l1}/{l2}: 没找到 {l3}')

print(f'\nA.1 树撤回: {removed_count}/{len(ADDED_PATHS)} 个节点')

# 2. 清空 row 中 a1l4 字段
# row 中可能挂在被删除的 L4 节点上，需要清空
cleared = 0
for c in data['contaminants']:
    name = c.get('contaminant', '')
    for item in c.get('items', []):
        if item.get('a1_l4', ''):
            item['a1_l4'] = ''
            cleared += 1
print(f'清空 a1_l4: {cleared} 条')

# 3. 检查 a1l3 - 酒类章节的「白酒」是 a1l3（不是 a1l4），需要特殊处理
# 「黄酒」是 a1l3=L3 节点，正确保留
# 「白酒」是 a1l3=L3 节点（在酒类→蒸馏酒→白酒 路径），但「蒸馏酒」是 L2
# 等等，让我重新看 row 字段
print()
print('=== 酒类章节 row a1l3 检查 ===')
for c in data['contaminants']:
    name = c.get('contaminant', '')
    for item in c.get('items', []):
        if item.get('a1_l1') == '酒类' and item.get('a1_l3') == '白酒':
            print(f'  [{name}] a1l1={item.get("a1_l1","")} a1l2={item.get("a1_l2","")} a1l3={item.get("a1_l3","")} a1l4={item.get("a1_l4","")}')

# 写回
with open(DATA, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'\n已保存')
