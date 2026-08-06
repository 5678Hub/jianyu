"""给 gb_checklist_subcat.json / gb_checklist.json 每个 subcategory 项加 *_id 字段

按 ChatGPT 审查建议：建立正式的 category_id / subcategory_id / table_id 字段
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

    # 建 table_id 反向索引：(big_id, table_no_normalized, sub_name) → table_id
    # 用于跨大类续编：同 (table_no, sub_name) → table_id
    table_lookup = {}
    table_by_no_sub = {}
    for t in table_ids['tables']:
        key = (t['big_category_id'], t['table_no_normalized'], t['subcategory_name'])
        table_by_no_sub[key] = t['id']

    # 1. 升级 gb_checklist_subcat.json
    gbs_path = os.path.join(root, 'data/current_period/gb_checklist_subcat.json')
    gbs = json.load(open(gbs_path, encoding='utf-8'))
    enriched = 0
    missing_tid = []
    for big_name, subs in gbs.get('categories', {}).items():
        big_id = big_by_name.get(big_name)
        if not big_id:
            continue
        for sub in subs:
            if not isinstance(sub, dict):
                continue
            sub_name = sub.get('name', '')
            table_no = sub.get('table_no', '')
            norm_no = table_no.lstrip('表')

            # big_category_id
            sub['big_category_id'] = big_id
            sub['big_category_name'] = big_name

            # subcategory_id（按 big_name|||sub_name 反查）
            sub_id = sub_by_pair.get(f'{big_name}|||{sub_name}')
            if sub_id:
                sub['subcategory_id'] = sub_id
            else:
                # 没有 subcategory_id 映射时，动态生成
                # 例：可可及焙烤咖啡产品 / 可可制品 → cocoa_coffee_products-cocoa_products
                # 暂时占位，后续手动校对
                sub['subcategory_id'] = f'{big_id}__{sub_name}'

            # table_id（精确查 (big_id, norm_no, sub_name)）
            tid = table_by_no_sub.get((big_id, norm_no, sub_name))
            if tid:
                sub['table_id'] = tid
            else:
                missing_tid.append(f'{big_name} / {sub_name} / {table_no}')
                sub['table_id'] = None

            # 升级 _meta 加 schema_version
            enriched += 1

    # 升级 _meta
    gbs['_meta']['schema_version'] = '1.1'
    gbs['_meta']['last_updated'] = '2026-08-06 10:05:00+08:00'
    gbs['_meta']['description'] = (
        'GB 2026 食品安全监督抽检实施细则 38 大类 / 253 张检验项目表；'
        '每条 sub 含 *_id 字段（big_category_id / subcategory_id / table_id）'
    )
    gbs['_meta']['item_schema'] = {
        'subcategory_id': 'str  稳定英文 slug ID',
        'big_category_id': 'str  稳定英文 slug ID',
        'big_category_name': 'str  大类中文名（展示用）',
        'table_id': 'str  稳定 table_id（见 table_ids.json）',
        'table_no': 'str  PDF 原始编号（展示用）',
        'table_name': 'str  表名',
        'name': 'str  细类名（中文）',
        'page': 'int  PDF 页码',
        'items': 'list  检验项目 [{序号, 检验项目, 依据法律法规或标准, 检测方法, 注脚}]',
    }

    open(gbs_path, 'w', encoding='utf-8').write(
        json.dumps(gbs, ensure_ascii=False, indent=2)
    )
    print(f'✅ gb_checklist_subcat.json 升级 schema v1.1')
    print(f'   enriched: {enriched} 张表')
    if missing_tid:
        print(f'⚠️ {len(missing_tid)} 条 table_id 未匹配（理论上不应发生）:')
        for x in missing_tid[:5]:
            print(f'  {x}')


if __name__ == '__main__':
    main()