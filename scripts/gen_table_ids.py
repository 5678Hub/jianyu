"""生成 table_ids.json（gb_checklist_subcat.json 的 253 张表 → 稳定 ID + 跨大类续编规范）"""
import json
import os


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ids = json.load(open(os.path.join(root, 'data/category_ids.json'), encoding='utf-8'))
    by_name = ids['by_name']
    gc = json.load(open(os.path.join(root, 'data/current_period/gb_checklist_subcat.json'), encoding='utf-8'))

    STANDARD_VERSION = 'gb2026'

    # 收集所有 (table_no, big_category_id, sub_name, sub_slug, page) → 自动生成 table_id
    raw_tables = []
    for big_name, subs in gc['categories'].items():
        big_id = by_name.get(big_name)
        if not big_id:
            print(f'⚠️ big_category 未映射: {big_name}')
            continue
        for s in subs:
            raw_tables.append({
                'table_no': s['table_no'],
                'table_name': s['table_name'],
                'sub_name': s['name'],
                'big_name': big_name,
                'big_id': big_id,
                'page': s.get('page'),
                'item_count': len(s.get('items', [])),
            })

    # 按 table_no 分组，找重复（跨大类续编）
    from collections import defaultdict
    by_table_no = defaultdict(list)
    for t in raw_tables:
        by_table_no[t['table_no']].append(t)

    # 生成 table_id（处理跨大类续编：加 sub_slug 后缀）
    table_list = []
    for table_no, group in sorted(by_table_no.items()):
        # 规范 table_no
        norm_no = table_no.lstrip('表')  # '33-8'
        is_multi = len(group) > 1
        for t in group:
            if is_multi:
                # 跨大类续编：加 sub_slug
                sub_slug = simplify_sub_for_table(t['sub_name'])
                tid = f'{STANDARD_VERSION}-{t["big_id"]}-{norm_no}-{sub_slug}'
            else:
                # 唯一表
                tid = f'{STANDARD_VERSION}-{t["big_id"]}-{norm_no}'
            t['__tid'] = tid
            table_list.append({
                'id': t['__tid'],
                'table_no': t['table_no'],
                'table_no_normalized': norm_no,
                'table_name': t['table_name'],
                'subcategory_name': t['sub_name'],
                'big_category_id': t['big_id'],
                'big_category_name': t['big_name'],
                'standard_version': STANDARD_VERSION,
                'page': t['page'],
                'item_count': t['item_count'],
                'continuation_of': None,  # 同 table_no 的第一个 id
                'source_file': 'data/current_period/gb_checklist_subcat.json',
            })

    # 处理 continuation_of
    no_to_first = {}
    for t in table_list:
        no = t['table_no']
        if no not in no_to_first:
            no_to_first[no] = t['id']
    for t in table_list:
        first_id = no_to_first[t['table_no']]
        if t['id'] != first_id:
            t['continuation_of'] = first_id

    # 写文件
    out = {
        '_meta': {
            'schema_version': '1.0',
            'last_updated': '2026-08-06 09:55:00+08:00',
            'description': '253 张 GB 2026 检验项目表 → 稳定 table_id。跨大类续编（19-2 / 19-3 / 33-8）加 sub_name 区分；continuation_of 指向同 table_no 的第一张',
            'standard_version': STANDARD_VERSION,
            'count': len(table_list),
        },
        'tables': table_list,
        'by_table_no': {
            t['table_no']: t['id'] for t in table_list
        },
        'continuation_groups': {
            no: [t['id'] for t in table_list if t['table_no'] == no]
            for no in no_to_first if sum(1 for t in table_list if t['table_no'] == no) > 1
        },
    }
    out_path = os.path.join(root, 'data/table_ids.json')
    open(out_path, 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print(f'✅ table_ids.json 写入 {len(table_list)} 条')
    print(f'   跨大类续编: {len(out["continuation_groups"])} 组')
    for no, tids in out['continuation_groups'].items():
        print(f'   {no}: {tids}')


def simplify_sub_for_table(name):
    """简化 sub_name 用作 table_id 后缀（仅 ASCII / 拼音友好字符）"""
    # 简化映射（手动，覆盖跨大类续编涉及的 sub）
    SIMPLIFY = {
        '干蛋制品': 'dry_egg_products',
        '冰蛋制品': 'frozen_egg_products',
        '液蛋制品': 'liquid_egg_products',
        '热凝固蛋制品': 'heat_coagulated_egg_products',
        '其他蛋制品': 'other_egg_products',
        '猪肝': 'pork_liver',
        '其他水产品': 'other_aquatic_products',
    }
    return SIMPLIFY.get(name, name.lower().replace(' ', '_'))


if __name__ == '__main__':
    main()