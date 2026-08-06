"""给 subcat_to_items.json 每个 alias 加 big_category_id / subcategory_id / table_id

与 category_ids.json / subcategory_ids.json / table_ids.json 关联
"""
import json
import os


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cat_ids = json.load(open(os.path.join(root, 'data/category_ids.json'), encoding='utf-8'))
    sub_ids = json.load(open(os.path.join(root, 'data/subcategory_ids.json'), encoding='utf-8'))
    table_ids = json.load(open(os.path.join(root, 'data/table_ids.json'), encoding='utf-8'))

    big_by_name = cat_ids['by_name']
    sub_by_pair = sub_ids['by_big_sub']

    # table 反向索引 (big_id, norm_no, sub_name) → table_id
    table_lookup = {}
    for t in table_ids['tables']:
        key = (t['big_category_id'], t['table_no_normalized'], t['subcategory_name'])
        table_lookup[key] = t['id']

    path = os.path.join(root, 'data/subcat_to_items.json')
    d = json.load(open(path, encoding='utf-8'))
    aliases = d.get('aliases', {})

    enriched = 0
    for alias, info in aliases.items():
        big = info.get('big_category', '')
        sub = info.get('subcategory', '')
        tno = info.get('table_no', '')
        norm_no = tno.lstrip('表')

        big_id = big_by_name.get(big)
        sub_id = sub_by_pair.get(f'{big}|||{sub}')

        if big_id:
            info['big_category_id'] = big_id
        if sub_id:
            info['subcategory_id'] = sub_id

        # table_id：精确查 (big_id, norm_no, sub)
        if big_id and norm_no and sub:
            tid = table_lookup.get((big_id, norm_no, sub))
            if tid:
                info['table_id'] = tid
            else:
                info['table_id'] = None
        else:
            info['table_id'] = None

        enriched += 1

    # 升级 _meta
    d['_meta']['schema_version'] = '1.1'
    d['_meta']['last_updated'] = '2026-08-06 10:15:00+08:00'
    d['_meta']['alias_count'] = len(aliases)
    d['_meta']['description'] = (
        '食品名/别名 → 大类+细类+表号的反向索引；'
        '含 big_category_id / subcategory_id / table_id 字段'
    )
    d['_meta']['alias_schema'] = {
        'big_category': 'str  [deprecated] 大类中文名',
        'subcategory': 'str  [deprecated] 细类中文名',
        'table_no': 'str  [deprecated] PDF 表号',
        'big_category_id': 'str  稳定英文 slug 大类 ID',
        'subcategory_id': 'str  稳定英文 slug 细类 ID',
        'table_id': 'str  稳定 table_id（见 table_ids.json）',
    }

    open(path, 'w', encoding='utf-8').write(
        json.dumps(d, ensure_ascii=False, indent=2)
    )
    print(f'✅ subcat_to_items.json 升级 schema v1.1')
    print(f'   enriched: {enriched} 条 alias')


if __name__ == '__main__':
    main()