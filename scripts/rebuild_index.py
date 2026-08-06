"""重建 master.json —— 加 record id + µ/μ 归一化 + 索引去重

新结构（schema v1.1）：
  records: [{id, ...fields}]         # 唯一实体，含 id
  indexes:
    by_canonical: {canonical_name -> {ids: [...], count, big_categories, food_names}}
    by_category:  {big_category     -> {ids: [...], count, foods, items}}
    by_item:      {item_name        -> {ids: [...], count, foods, big_categories}}
  project_weight: 保留
  _meta: {schema_version: '1.1', data_version, ...}

⚠️ 索引只存 record_id，不再存完整 record 副本（节约约 1.6MB / 53% 体积）
"""
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from etl_common import (
    make_record_id, normalize_failed_items, normalize_mu, jsonable, save_json, load_json,
)

BJ = timezone(timedelta(hours=8))
NOW = datetime.now(BJ).strftime('%Y-%m-%d %H:%M:%S+08:00')
DATA_VERSION = datetime.now(BJ).strftime('%Y.%m.%d.%H%M')

p = r"C:\Users\10487\WorkBuddy\jianyu\data\master.json"
d = load_json(p)
records = d['records']

# ============================================================
# Step 1: 给每条 record 加 id（兼容已有 id 不覆盖）
# ============================================================
missing_ids = [r for r in records if not r.get('id')]
if missing_ids:
    # 按当前顺序补 r0001+（稳定：每次跑结果一致）
    for i, r in enumerate(records):
        if not r.get('id'):
            r['id'] = make_record_id(i)
    print(f"[1] 给 {len(missing_ids)} 条 record 补 id")
else:
    print(f"[1] 全部 {len(records)} 条 record 已有 id，跳过")

# ============================================================
# Step 2: µ/μ 归一化（failed_items.limit + result + fail_raw）
# ============================================================
changed_items = 0
changed_raw = 0
for r in records:
    fis = r.get('failed_items', [])
    new_fis = normalize_failed_items(fis)
    if new_fis != fis:
        r['failed_items'] = new_fis
        changed_items += 1
    # fail_raw 也归一化（公告原文里残留的 Greek μ）
    fr = r.get('fail_raw', '')
    if fr and '\u03bc' in fr:
        r['fail_raw'] = normalize_mu(fr)
        changed_raw += 1
print(f"[2] µ/μ 归一化：修改 {changed_items} 条 failed_items + {changed_raw} 条 fail_raw")

# ============================================================
# Step 3: 重建索引（只存 id + 聚合信息）
# ============================================================
by_canonical = defaultdict(lambda: {'ids': [], 'count': 0, 'big_categories': set(), 'food_names': set()})
by_category = defaultdict(lambda: {'ids': [], 'count': 0, 'foods': set(), 'items': set()})
by_item = defaultdict(lambda: {'ids': [], 'count': 0, 'foods': set(), 'big_categories': set()})

for r in records:
    rid = r['id']
    canon = r.get('food_name_canonical') or r.get('food_name_raw') or ''
    big = r.get('big_category') or ''

    # by_canonical
    by_canonical[canon]['ids'].append(rid)
    by_canonical[canon]['count'] += 1
    by_canonical[canon]['big_categories'].add(big)
    by_canonical[canon]['food_names'].add(r.get('food_name_raw', ''))

    # by_category
    by_category[big]['ids'].append(rid)
    by_category[big]['count'] += 1
    by_category[big]['foods'].add(r.get('food_name_raw', ''))
    for fi in r.get('failed_items', []):
        if fi.get('item'):
            by_category[big]['items'].add(fi['item'])

    # by_item
    for fi in r.get('failed_items', []):
        item = fi.get('item')
        if not item:
            continue
        by_item[item]['ids'].append(rid)
        by_item[item]['count'] += 1
        by_item[item]['foods'].add(r.get('food_name_raw', ''))
        by_item[item]['big_categories'].add(big)

# 旧 key 是 by_canonical / by_category / by_item，统一改到 indexes 下
d['indexes'] = {
    'by_canonical': jsonable(dict(by_canonical)),
    'by_category':  jsonable(dict(by_category)),
    'by_item':      jsonable(dict(by_item)),
}
# 兼容旧 key（前端如果还读老 key 不会爆）
d['by_canonical'] = d['indexes']['by_canonical']
d['by_category']  = d['indexes']['by_category']
d['by_item']      = d['indexes']['by_item']

# ============================================================
# Step 4: 更新 _meta
# ============================================================
d['_meta']['schema_version'] = '1.1'
d['_meta']['last_updated'] = NOW
d['_meta']['data_version'] = DATA_VERSION
d['_meta']['record_count'] = len(records)
d['_meta']['by_canonical_count'] = len(d['indexes']['by_canonical'])
d['_meta']['by_category_count']  = len(d['indexes']['by_category'])
d['_meta']['by_item_count']      = len(d['indexes']['by_item'])
d['_meta']['project_weight_count'] = len(d.get('project_weight', {}))
d['_meta']['index_rebuilt'] = NOW
d['_meta']['index_schema'] = {
    'by_canonical': 'dict[canonical_name] -> {ids: list[record_id], count, big_categories, food_names}',
    'by_category':  'dict[big_category]     -> {ids: list[record_id], count, foods, items}',
    'by_item':      'dict[item_name]        -> {ids: list[record_id], count, foods, big_categories}',
}
d['_meta']['record_schema']['id'] = 'str  唯一 record id（r0001 格式）'

save_json(p, d)

print()
print(f"✅ master.json 已重建")
print(f"  records: {len(records)}")
print(f"  by_canonical: {len(d['indexes']['by_canonical'])}")
print(f"  by_category:  {len(d['indexes']['by_category'])}")
print(f"  by_item:      {len(d['indexes']['by_item'])}")
print(f"  project_weight: {len(d.get('project_weight', {}))}")
print(f"  schema_version: {d['_meta']['schema_version']}")
print(f"  data_version:   {d['_meta']['data_version']}")

# ============================================================
# Step 5: 同步 sw.js 的 DATA_VERSION
# ============================================================
sw_path = os.path.join(os.path.dirname(p), '..', 'sw.js')
sw_path = os.path.abspath(sw_path)
if os.path.exists(sw_path):
    sw_src = open(sw_path, encoding='utf-8').read()
    import re
    new_sw = re.sub(
        r"const DATA_VERSION = '[^']*';",
        f"const DATA_VERSION = '{DATA_VERSION}';",
        sw_src,
    )
    if new_sw != sw_src:
        open(sw_path, 'w', encoding='utf-8').write(new_sw)
        print(f"✅ sw.js  DATA_VERSION → {DATA_VERSION}")
    else:
        print(f"ℹ️ sw.js  DATA_VERSION 未变化")
else:
    print(f"⚠️ sw.js 未找到：{sw_path}")