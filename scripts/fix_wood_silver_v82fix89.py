#!/usr/bin/env python3
"""v82-fix89: 补 5 条缺挂 row

挂载规则（基于 v82-final 设计）：
- 「木耳及其制品、银耳及其制品」 row 应该三挂到三个 L3 节点：
  - a1l3=木耳 （毛木耳,黑木耳）
  - a1l3=银耳
  - a1l3=其他食用菌制品
- 当前缺挂 5 条：补挂到缺失节点
"""
import json
import copy
from pathlib import Path

DATA = Path('data/gb2762/gb2762_2025.json')

with open(DATA, encoding='utf-8') as f:
    data = json.load(f)

# 收集现有 (pollutant, limit_value) -> template row
target_food = '木耳及其制品、银耳及其制品'
template_rows = {}  # (pol, limit_value) -> template (with a1l3=木耳 or 其他食用菌制品)
for c in data['contaminants']:
    name = c.get('contaminant','')
    for item in c.get('items',[]):
        food = item.get('food','')
        if food == target_food:
            lv = str(item.get('limit_value','')).strip()
            template_rows[(name, lv)] = item

# 缺挂定义：(pollutant, limit_value, 目标 a1l3)
missing_targets = [
    ('铅', '1.0', '银耳'),
    ('镉', '0.5', '其他食用菌制品'),
    ('汞', '—', '银耳'),
    ('汞', '0.1', '银耳'),
    ('砷', '—', '其他食用菌制品'),
]

# 找所属污染物表
contaminants_by_name = {c.get('contaminant',''): c for c in data['contaminants']}

added = []
for pol, lv, target_node in missing_targets:
    key = (pol, lv)
    if key not in template_rows:
        print(f'[SKIP] {pol} limit={lv} 没找到模板')
        continue
    if pol not in contaminants_by_name:
        print(f'[SKIP] {pol} 不在污染物表中')
        continue

    # 复制模板并修改 a1l3
    new_row = copy.deepcopy(template_rows[key])
    new_row['a1_l3'] = target_node
    new_row['a1_l4'] = ''

    # 检查是否已存在（避免重复挂载）
    already = False
    for exist in contaminants_by_name[pol].get('items',[]):
        if (exist.get('food','') == new_row['food']
            and str(exist.get('limit_value','')).strip() == lv
            and exist.get('a1_l3','') == target_node):
            already = True
            break
    if already:
        print(f'[SKIP] {pol} limit={lv} a1l3={target_node} 已挂载')
        continue

    contaminants_by_name[pol]['items'].append(new_row)
    added.append((pol, lv, target_node))
    print(f'[ADD] {pol} limit={lv} a1l3={target_node}')

# 备份
backup_path = DATA.with_suffix('.json.bak.v82fix89_wood_silver')
with open(backup_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'\n备份: {backup_path}')

# 写回
with open(DATA, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\n总计补挂 {len(added)} 条 row:')
for pol, lv, n in added:
    print(f'  {pol} {lv} mg/kg → a1l3={n}')
