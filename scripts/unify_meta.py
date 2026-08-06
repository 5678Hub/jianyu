"""jianyu JSON 数据库统一整理脚本"""
import json, os
from datetime import datetime, timezone, timedelta

BJ = timezone(timedelta(hours=8))
NOW = datetime.now(BJ).strftime('%Y-%m-%d %H:%M:%S+08:00')

ROOT = r"C:\Users\10487\WorkBuddy\jianyu"

def save(path, data):
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def add_meta(d, **kwargs):
    base = {
        'schema_version': '1.0',
        'last_updated': NOW,
        'encoding': 'UTF-8',
        'bom': False,
        'source': '食品安全监督抽检实施细则（2026年版）',
        'origin': 'jianyu 食品安全抽检风险查询',
    }
    base.update(kwargs)
    d['_meta'] = base
    return d

# 1. master.json
p = os.path.join(ROOT, 'data/master.json')
d = json.load(open(p, encoding='utf-8'))
n = len(d.get('records', []))
add_meta(d,
    source='山东/辽宁/重庆 28+8 期抽检公告汇总',
    record_count=n,
    by_canonical_count=len(d.get('by_canonical', {})),
    by_category_count=len(d.get('by_category', {})),
    by_item_count=len(d.get('by_item', {})),
    project_weight_count=len(d.get('project_weight', {})),
    description='历史不合格明细主库，含 records 和预建索引',
    record_schema={
        'source': 'str  来源省份',
        'food_name_raw': 'str  原始食品名（公告原文）',
        'food_name_canonical': 'str  规范食品名（按分类映射）',
        'big_category': 'str  大类',
        'sub_category': 'str  细类（"大类-细类"形式）',
        'category': 'str  大类全称',
        'sampler_name': 'str  抽样单位',
        'sampler_addr': 'str  抽样单位地址',
        'prod_date': 'str  生产日期',
        'prod_name': 'str  标称生产单位',
        'prod_addr': 'str  标称生产单位地址',
        'fail_raw': 'str  原始不合格字符串',
        'failed_items': 'list[dict]  不合格项 [{item, result, limit}]',
        'bulletin_no': 'str  公告编号',
    },
    index_schema={
        'by_canonical': 'dict[canonical_name] -> {records, count, ...}',
        'by_category': 'dict[big_category] -> {records, count, foods: set}',
        'by_item': 'dict[item_name] -> {records, count, ...}',
        'project_weight': 'dict[项目名] -> 权重信息',
    },
)
save(p, d)
print(f'✅ master.json  records={n}')

# 2. categories_2026.json
p = os.path.join(ROOT, 'data/categories_2026.json')
d = json.load(open(p, encoding='utf-8'))
old_source = d.pop('_source', None)
old_note = d.pop('_note', None)
cats = d.get('categories', [])
add_meta(d,
    source=old_source or '食品安全监督抽检实施细则（2026年版）目录',
    note=old_note or '三十一餐饮食品 + 三十三~三十九食用农产品系列',
    category_count=len(cats),
    available_count=sum(1 for c in cats if c.get('available')),
    description='大类骨架（39 大类，不含细类），前端用作大类卡片',
    category_schema={
        'no': 'str  中文编号（一/二/...）',
        'name': 'str  大类名',
        'available': 'bool  前端是否展示',
    },
)
save(p, d)
print(f'✅ categories_2026.json  大类={len(cats)}')

# 3. categories_2026_full.json - legacy
p = os.path.join(ROOT, 'data/categories_2026_full.json')
d = json.load(open(p, encoding='utf-8'))
old_source = d.pop('_source', None)
cats = d.get('categories', [])
with_sub = [c for c in cats if c.get('subcategories')]
total_sub = sum(len(c.get('subcategories', [])) for c in cats)
add_meta(d,
    source=old_source or '食品安全监督抽检实施细则（2026年版）',
    category_count=len(cats),
    with_subcategories_count=len(with_sub),
    total_subcategory_count=total_sub,
    status='legacy',
    deprecation_note='前端未引用此文件（前端用 categories_2026.json 取大类骨架，gb_checklist_subcat.json 取细类+检验项目）。保留供历史兼容/迁移参考。',
    description='大类 + 细类 展开版（含 subcategories），legacy',
    category_schema={
        'no': 'str  中文编号',
        'name': 'str  大类名',
        'available': 'bool',
        'subcategories': 'list[{code, no, name}]  细类',
    },
)
save(p, d)
print(f'✅ categories_2026_full.json  legacy  大类={len(cats)} 细类={total_sub}')

# 4. categories_subcat.json - superseded
p = os.path.join(ROOT, 'data/categories_subcat.json')
d = json.load(open(p, encoding='utf-8'))
if isinstance(d, dict):
    add_meta(d,
        source='食品安全监督抽检实施细则（2026年版）',
        source_file=d.get('source_file', ''),
        structure=d.get('structure', '大类→细类/表→检验项目'),
        table_count=d.get('table_count', 0),
        category_count=d.get('category_count', 0),
        status='superseded',
        superseded_by='current_period/gb_checklist_subcat.json',
        deprecation_note='内容与 current_period/gb_checklist_subcat.json 重复（PDF 解析早期版本）。前端使用 gb_checklist_subcat.json。建议删除。',
        description='PDF 解析早期版（已由 gb_checklist_subcat.json 取代）',
    )
save(p, d)
print(f'✅ categories_subcat.json  superseded')

# 5. category_map.json
p = os.path.join(ROOT, 'data/category_map.json')
d = json.load(open(p, encoding='utf-8'))
old_comment = d.pop('_comment', None)
old_source = d.pop('_source', None)
old_version = d.pop('_version', None)
cat_keys = [k for k in d.keys() if not k.startswith('_')]
total_aliases = sum(len(v) for v in d.values() if isinstance(v, list))
add_meta(d,
    source=old_source or '2026 实施细则目录 + 食品分类系统 + 山东/辽宁/重庆公告反推',
    version=old_version or 'v2.1 (2026-08-04, +淡水鱼/桑葚/糖果/罐头/黑木耳)',
    note=old_comment or '食品名 → "大类-细类"映射',
    category_count=len(cat_keys),
    total_alias_count=total_aliases,
    description='食品名/别名 → 大类-细类 映射（按 2026 实施细则 38 大类）',
    schema='dict["大类-细类"] -> list[食品名/别名]',
)
save(p, d)
print(f'✅ category_map.json  类别={len(cat_keys)} 别名={total_aliases}')

# 6. subcat_to_items.json
p = os.path.join(ROOT, 'data/subcat_to_items.json')
d = json.load(open(p, encoding='utf-8'))
old_source = d.pop('source', None)
aliases = d.get('aliases', {})
add_meta(d,
    source=old_source or '食品安全监督抽检实施细则（2026年版）',
    alias_count=len(aliases),
    description='食品名别名 → 规范食品名 映射（用于搜索匹配）',
    schema='{aliases: dict[别名] -> 规范名}',
    misnamed_field_warning='文件名 subcat_to_items 易误导——实际是品名→规范名映射，不是细类→项目映射',
)
save(p, d)
print(f'✅ subcat_to_items.json  aliases={len(aliases)}')

# 7. synonyms.json
p = os.path.join(ROOT, 'data/synonyms.json')
d = json.load(open(p, encoding='utf-8'))
old_comment = d.pop('_comment', None)
old_version = d.pop('_version', None)
old_principles = d.pop('_principles', None)
rules = d.get('rules', [])
add_meta(d,
    source='jianyu 同义词规则集（手工维护 + 数据反推）',
    version=old_version or 'v1.2 (2026-08-04, +5 项山药/辣椒/桑葚小品种)',
    note=old_comment or '同义词词典：抽检食品名 → 规范食品名',
    principles=old_principles or [],
    rule_count=len(rules),
    description='同义词规则集',
    schema='{rules: list[ {pattern, replacement, ...} ]}',
)
save(p, d)
print(f'✅ synonyms.json  rules={len(rules)}')

# 8. gb_checklist.json
p = os.path.join(ROOT, 'data/current_period/gb_checklist.json')
d = json.load(open(p, encoding='utf-8'))
old_period = d.pop('_period', None)
old_note = d.pop('_note', None)
old_source = d.pop('_source_file', None)
d.pop('_meta', None)
cats = d.get('categories', [])
add_meta(d,
    source=f'{old_source or "（2026年第8期）.doc"}（本期公告）',
    period=old_period or '2026年第8期',
    note=old_note or '本期公告检验项目（参考性；2026 抽检细则 PDF 已更细）',
    category_count=len(cats),
    description='本期国抽公告附件1检验项目',
    schema='{categories: dict[big_category] -> [tables]}',
)
save(p, d)
print(f'✅ gb_checklist.json  大类={len(cats)}')

# 9. gb_checklist_subcat.json
p = os.path.join(ROOT, 'data/current_period/gb_checklist_subcat.json')
d = json.load(open(p, encoding='utf-8'))
old_source = d.pop('source', None)
cats = d.get('categories', {})
total_tables = sum(len(v) for v in cats.values())
add_meta(d,
    source=old_source or '食品安全监督抽检实施细则（2026年版）',
    category_count=len(cats),
    table_count=total_tables,
    description='细类 + 检验项目 权威数据（PDF 解析），前端实际驱动"X 细类"角标和细类列表',
    schema='{categories: dict[大类] -> [tables], table: {name, table_no, table_name, items, notes}}',
    item_schema={
        '序号': 'int',
        '检验项目': 'str',
        '依据法律法规或标准': 'str',
        '检测方法': 'str',
    },
)
save(p, d)
print(f'✅ gb_checklist_subcat.json  大类={len(cats)} 表={total_tables}')

print()
print('='*60)
print('所有核心 JSON 的 _meta 已统一')
print('='*60)