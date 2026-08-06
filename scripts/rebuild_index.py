"""重建 master.json 的索引（by_canonical / by_category / by_item）"""
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta

BJ = timezone(timedelta(hours=8))
NOW = datetime.now(BJ).strftime('%Y-%m-%d %H:%M:%S+08:00')

p = r"C:\Users\10487\WorkBuddy\jianyu\data\master.json"
d = json.load(open(p, encoding='utf-8'))
records = d['records']

# 重建索引
by_canonical = defaultdict(lambda: {'records': [], 'count': 0, 'big_categories': set(), 'food_names': set()})
by_category = defaultdict(lambda: {'records': [], 'count': 0, 'foods': set(), 'items': set()})
by_item = defaultdict(lambda: {'records': [], 'count': 0, 'foods': set(), 'big_categories': set()})

for r in records:
    canon = r.get('food_name_canonical') or r.get('food_name_raw') or ''
    big = r.get('big_category') or ''

    # by_canonical
    by_canonical[canon]['records'].append(r)
    by_canonical[canon]['count'] += 1
    by_canonical[canon]['big_categories'].add(big)
    by_canonical[canon]['food_names'].add(r.get('food_name_raw', ''))

    # by_category
    by_category[big]['records'].append(r)
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
        by_item[item]['records'].append(r)
        by_item[item]['count'] += 1
        by_item[item]['foods'].add(r.get('food_name_raw', ''))
        by_item[item]['big_categories'].add(big)

# 序列化 set -> sorted list
def to_jsonable(obj):
    if isinstance(obj, set):
        return sorted(list(obj))
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    return obj

d['by_canonical'] = to_jsonable(dict(by_canonical))
d['by_category'] = to_jsonable(dict(by_category))
d['by_item'] = to_jsonable(dict(by_item))

# 更新 _meta 计数
d['_meta']['last_updated'] = NOW
d['_meta']['by_canonical_count'] = len(d['by_canonical'])
d['_meta']['by_category_count'] = len(d['by_category'])
d['_meta']['by_item_count'] = len(d['by_item'])
d['_meta']['project_weight_count'] = len(d.get('project_weight', {}))
d['_meta']['index_rebuilt'] = NOW

json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print(f"✅ 索引已重建")
print(f"  records: {len(records)}")
print(f"  by_canonical: {len(d['by_canonical'])}")
print(f"  by_category: {len(d['by_category'])}")
print(f"  by_item: {len(d['by_item'])}")
print(f"  project_weight: {len(d.get('project_weight', {}))}")