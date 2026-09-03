#!/usr/bin/env python3
"""v82-fix90: 还原食用菌 A.1 树 + 清空食用菌章节 row a1l4"""
import json
import shutil

DATA = 'data/gb2762/gb2762_2025.json'

with open(DATA, encoding='utf-8') as f:
    data = json.load(f)

# 1. 备份
shutil.copy(DATA, DATA + '.bak.v82fix90_revert_tree')

# 2. 在 a1.tree 里直接找食用菌及其制品
a1_tree = data['appendix_a1']['tree']
target_root = None
for root in a1_tree:
    if root.get('name') == '食用菌及其制品':
        target_root = root
        break

if target_root is None:
    print('ERROR: 找不到「食用菌及其制品」根节点')
    raise SystemExit(1)

# 3. 找「食用菌制品」L2
shiyongjun_l2 = None
for c2 in target_root.get('children', []):
    if c2.get('name') == '食用菌制品':
        shiyongjun_l2 = c2
        break

if shiyongjun_l2 is None:
    print('ERROR: 找不到「食用菌制品」L2 节点')
    raise SystemExit(1)

# 4. 删除 v82-fix82 添加的 14 个 L3「制品」节点
wrong_l3_names = {
    '松茸制品', '松露制品', '牛肝菌制品', '鸡枞制品', '多汁乳菇制品',
    '羊肚菌制品', '獐头菌制品', '青头菌制品', '鸡油菌制品',
    '榛蘑制品', '姬松茸制品', '香菇制品', '木耳制品', '银耳制品'
}

before = len(shiyongjun_l2.get('children', []))
shiyongjun_l2['children'] = [
    c for c in shiyongjun_l2.get('children', [])
    if c.get('name') not in wrong_l3_names
]
after = len(shiyongjun_l2.get('children', []))

print(f'食用菌制品 L2 子节点: {before} → {after}')
for c in shiyongjun_l2['children']:
    print(f'  - {c.get("name")}')

# 5. 清空食用菌章节所有 row 的 a1l4 字段
cleared = 0
for c in data['contaminants']:
    name = c.get('contaminant', '')
    for item in c.get('items', []):
        if item.get('a1_l1', '').startswith('食用菌') and item.get('a1_l4', ''):
            item['a1_l4'] = ''
            cleared += 1
print(f'\n清空食用菌章节 row 的 a1l4: {cleared} 条')

# 6. 写回
with open(DATA, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'\n已保存到 {DATA}')
