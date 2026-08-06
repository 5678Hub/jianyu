"""升级 master.json 到 schema v1.2：record 顶层加 big_category_id / subcategory_id

旧字段（big_category / sub_category / category）保留 deprecated 标记。
"""
import json
import os


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    master_path = os.path.join(root, 'data/master.json')
    cat_ids = json.load(open(os.path.join(root, 'data/category_ids.json'), encoding='utf-8'))
    sub_ids = json.load(open(os.path.join(root, 'data/subcategory_ids.json'), encoding='utf-8'))

    big_by_name = cat_ids['by_name']
    sub_by_pair = sub_ids['by_big_sub']

    m = json.load(open(master_path, encoding='utf-8'))
    records = m['records']

    upgraded = 0
    failed_items_upgraded = 0
    missing_sub = []
    for r in records:
        big = r.get('big_category', '')
        sub = r.get('sub_category', '')
        # big_category_id
        big_id = big_by_name.get(big)
        if big_id:
            r['big_category_id'] = big_id
        else:
            missing_sub.append(f'big: {big}')
            continue

        # subcategory_id（按 big_name|||sub_name 反查）
        # sub_category 格式："大类-细类"
        if '-' in sub:
            sub_name = sub.split('-', 1)[1]
        else:
            sub_name = sub
        sub_id = sub_by_pair.get(f'{big}|||{sub_name}')
        if sub_id:
            r['subcategory_id'] = sub_id
        else:
            missing_sub.append(f'sub: {big}|||{sub_name}')

        # failed_items 也加 big_category_id / subcategory_id / table_id
        for fi in r.get('failed_items', []):
            if big_id:
                fi['big_category_id'] = big_id
            if sub_id:
                fi['subcategory_id'] = sub_id
            # table_id 留 null（数据源无表号信息，未来 ETL 阶段从公告附件补）
            if 'table_id' not in fi:
                fi['table_id'] = None
            failed_items_upgraded += 1

        upgraded += 1

    # 升级 _meta
    m['_meta']['schema_version'] = '1.2'
    m['_meta']['record_schema'] = {
        'id': 'str  record_id, jianyu 内部唯一 (r0001~rXXXX)',
        'big_category_id': 'str  稳定英文 slug 大类 ID（见 category_ids.json）',
        'subcategory_id': 'str  稳定英文 slug 细类 ID（见 subcategory_ids.json）',
        'big_category': 'str  [deprecated] 大类中文名，建议改用 big_category_id',
        'sub_category': 'str  [deprecated] 细类中文名"大类-细类"，建议改用 subcategory_id',
        'category': 'str  [deprecated] 大类全称，建议改用 big_category_id',
        'food_name_raw': 'str  原始食品名（公告原文）',
        'food_name_canonical': 'str  规范食品名（按分类映射）',
        'sampler_name': 'str  抽样单位',
        'sampler_addr': 'str  抽样单位地址',
        'prod_date': 'str  生产日期',
        'prod_name': 'str  标称生产单位',
        'prod_addr': 'str  标称生产单位地址',
        'fail_raw': 'str  原始不合格字符串（已 µ/μ 归一化）',
        'failed_items': 'list[dict]  不合格项 [{item, result, limit, limit_normalized, result_normalized, big_category_id, subcategory_id}]',
        'bulletin_no': 'str  公告编号',
        'source': 'str  来源省份',
    }

    # 输出
    open(master_path, 'w', encoding='utf-8').write(
        json.dumps(m, ensure_ascii=False, indent=2)
    )
    print(f'✅ master.json 升级到 schema v1.2')
    print(f'   升级 records: {upgraded}')
    print(f'   schema_version: {m["_meta"]["schema_version"]}')
    if missing_sub:
        print(f'⚠️ {len(set(missing_sub))} 个 (big, sub) 对未找到 subcategory_id:')
        for x in sorted(set(missing_sub))[:10]:
            print(f'  {x}')


if __name__ == '__main__':
    main()