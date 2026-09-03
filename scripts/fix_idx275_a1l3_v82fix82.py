"""v82-fix82 任务3 后续修复：idx=275 BaP「熏、烧、烤肉类」a1_l3 补 '熟肉制品'

问题：a1_l3 空导致 walkExact 注册到 tree 中同名 L3 节点「熏、烧、烤肉类」，
但 PDF 原文归属是「熟肉制品」L3 下的「熏、烧、烤肉类」L4 节点（4 层 PK）。

修复：a1_l3 改为 '熟肉制品'，walkExact 会注册到 4 层 PK
`肉及肉制品|肉制品（包括内脏制品、血制品）|熟肉制品|熏、烧、烤肉类`

副作用：
- 「熟肉制品 → 熏、烧、烤肉类」L4 节点 own 段：0 → 1 条 idx=275
- 同名 L3「熏、烧、烤肉类」节点 own 段：1 → 0（idx=275 不再注册到这）
  但 ancestorsLevels 段会显示 idx=275 fallback
- 净增 row 数: 0
"""
import json, shutil, os
from pathlib import Path

DATA_FILE = 'data/gb2762/gb2762_2025.json'
BACKUP_FILE = 'data/gb2762/gb2762_2025.json.bak.v82fix82_idx275_a1l3'

if not os.path.exists(BACKUP_FILE):
    shutil.copy2(DATA_FILE, BACKUP_FILE)
    print(f'备份: {BACKUP_FILE}')

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    d = json.load(f)

# 定位 idx=275
total = 0
target = None
target_path = None
for ci, con in enumerate(d['contaminants']):
    if con['table_no'] != 9: continue  # BaP 表
    for ii, it in enumerate(con['items']):
        total += 1
        if total == 275:
            target = it
            target_path = (ci, ii)
            break
    if target: break

assert target is not None, 'idx=275 未找到'
print(f'idx=275 修复前: a1_l3="{target.get("a1_l3","")}" a1_l4="{target.get("a1_l4","")}" food="{target["food"]}"')

# 修复
target['a1_l3'] = '熟肉制品'
print(f'idx=275 修复后: a1_l3="{target.get("a1_l3","")}" a1_l4="{target.get("a1_l4","")}"')

# 写回
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'已写回: {DATA_FILE}')
print(f'备份: {BACKUP_FILE}')
