"""v82-fix82: 复制挂载 idx=144 (镉 2.0 双壳贝类、腹足类、头足类、棘皮类) 到
- 软体动物→头足类 L4
- 软体动物→腹足类 L4

按 v82-fix80 多节点挂载风格：保留 food 字段原始「双壳贝类、腹足类、头足类、棘皮类」+ modif「去除内脏」+ val=2.0
仅修改 a1_l4 路径字段

新 idx:
- idx=145 → 头足类 L4
- idx=146 → 腹足类 L4
"""
import json
import os
import shutil

DATA_FILE = 'data/gb2762/gb2762_2025.json'
BACKUP_FILE = 'data/gb2762/gb2762_2025.json.bak.v82fix82_cephalopoda_gastropoda'

# 备份
if not os.path.exists(BACKUP_FILE):
    shutil.copy2(DATA_FILE, BACKUP_FILE)
    print(f'备份: {BACKUP_FILE}')

with open(DATA_FILE,'r',encoding='utf-8') as f:
    d = json.load(f)

# 定位 idx=144
total = 0
target = None
target_con_idx = None
target_item_idx = None
for ci, con in enumerate(d['contaminants']):
    for ii, it in enumerate(con['items']):
        total += 1
        if total == 144:
            target = it
            target_con_idx = ci
            target_item_idx = ii
            break

assert target is not None, 'idx=144 未找到'

# 复制 idx=144 → idx=145 (头足类)
new_145 = dict(target)
new_145['a1_l4'] = '头足类'

# 复制 idx=144 → idx=146 (腹足类)
new_146 = dict(target)
new_146['a1_l4'] = '腹足类'

# 插入到 contaminants[1].items (镉表) 在 idx=144 之后
con_cd = d['contaminants'][target_con_idx]
items = con_cd['items']
# 找到 items 数组中 idx=144 的实际位置
# 实际是 target_item_idx
# 在 target_item_idx+1 插入 new_145 + new_146
items.insert(target_item_idx + 1, new_145)
items.insert(target_item_idx + 2, new_146)

print(f'插入 idx=145 → 头足类: food={new_145["food"]} val={new_145["limit_value"]} modif={new_145["modif"]}')
print(f'插入 idx=146 → 腹足类: food={new_146["food"]} val={new_146["limit_value"]} modif={new_146["modif"]}')

# 验证
new_total = sum(len(con['items']) for con in d['contaminants'])
print(f'总 items: 288 → {new_total}')

# 写回
with open(DATA_FILE,'w',encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'已写回: {DATA_FILE}')
print(f'备份: {BACKUP_FILE}')
