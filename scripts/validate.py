"""jianyu 发布前校验脚本

检查项（任一失败 exit code=1）：
  ✅ 所有核心 JSON 有 _meta.schema_version
  ✅ 所有 record id 唯一
  ✅ 索引引用的 id 在 records 中都存在
  ✅ µ (U+00B5) 和 μ (U+03BC) 不得混用（发布前必须 ETL 归一化）

警告项（exit code=0，仅提示）：
  ⚠️ 表号重复（一个 table_no 出现在多个分类）

用法：python validate.py [--root <path>] [--strict]
"""
import argparse
import json
import os
import sys

ROOT_DEFAULT = r"C:\Users\10487\WorkBuddy\jianyu"

# 必须有 _meta.schema_version 的核心 JSON
CORE_JSONS = [
    'data/master.json',
    'data/categories_2026.json',
    'data/categories_2026_full.json',
    'data/categories_subcat.json',
    'data/category_map.json',
    'data/subcat_to_items.json',
    'data/synonyms.json',
    'data/current_period/gb_checklist.json',
    'data/current_period/gb_checklist_subcat.json',
]

MU_MICRO = '\u00b5'
MU_GREEK = '\u03bc'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=ROOT_DEFAULT)
    ap.add_argument('--strict', action='store_true', help='警告也视作失败')
    args = ap.parse_args()

    root = args.root
    failures = []
    warnings = []

    print(f"🔍 jianyu 数据校验  root={root}\n")

    # ============================================================
    # 1. _meta.schema_version 必填
    # ============================================================
    print("[1] _meta.schema_version 必填检查")
    for rel in CORE_JSONS:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            failures.append(f"❌ {rel}  文件不存在")
            continue
        try:
            d = json.load(open(path, encoding='utf-8'))
        except Exception as e:
            failures.append(f"❌ {rel}  JSON 解析失败：{e}")
            continue
        meta = d.get('_meta') if isinstance(d, dict) else None
        if not meta or not meta.get('schema_version'):
            failures.append(f"❌ {rel}  缺 _meta.schema_version")
        else:
            print(f"  ✅ {rel}  schema_version={meta['schema_version']}")

    # ============================================================
    # 2. master.json 专用检查
    # ============================================================
    print("\n[2] master.json 专用检查")
    master_path = os.path.join(root, 'data/master.json')
    if not os.path.exists(master_path):
        failures.append("❌ master.json 不存在")
    else:
        m = json.load(open(master_path, encoding='utf-8'))
        records = m.get('records', [])
        indexes = m.get('indexes', {})

        # 2.1 record id 唯一
        ids = [r.get('id') for r in records]
        no_id = [i for i, r in enumerate(records) if not r.get('id')]
        dup_ids = [i for i in set(ids) if ids.count(i) > 1]
        if no_id:
            failures.append(f"❌ master.json  {len(no_id)} 条 record 缺 id")
        elif dup_ids:
            failures.append(f"❌ master.json  record id 重复：{dup_ids}")
        else:
            print(f"  ✅ record id 唯一  共 {len(ids)} 条")

        # 2.2 索引引用合法性
        id_set = set(ids)
        for idx_name in ['by_canonical', 'by_category', 'by_item']:
            idx = indexes.get(idx_name, {})
            if not idx:
                warnings.append(f"⚠️ 索引 {idx_name} 为空或缺失")
                continue
            # 检查每个 entry 含 ids 字段
            bad_shape = [k for k, v in idx.items() if not isinstance(v, dict) or 'ids' not in v]
            if bad_shape:
                failures.append(f"❌ {idx_name}  {len(bad_shape)} 条 entry 缺 'ids' 字段")
            # 检查 ids 是否都引用了真实 record
            missing_refs = set()
            for k, v in idx.items():
                for rid in v.get('ids', []):
                    if rid not in id_set:
                        missing_refs.add((k, rid))
            if missing_refs:
                failures.append(f"❌ {idx_name}  {len(missing_refs)} 条引用了不存在的 record id")
                # 列出前 5 个
                for k, rid in list(missing_refs)[:5]:
                    failures.append(f"     - {idx_name}[{k!r}] -> {rid!r}")
            else:
                print(f"  ✅ {idx_name}  {len(idx)} key，全部 id 引用合法")

        # 2.2b *_id 字段检查（schema v1.2+）
        print("\n[2b] *_id 字段覆盖率（schema v1.2+）")
        cat_ids = json.load(open(os.path.join(root, 'data/category_ids.json'), encoding='utf-8'))
        sub_ids = json.load(open(os.path.join(root, 'data/subcategory_ids.json'), encoding='utf-8'))
        big_id_set = set(c['id'] for c in cat_ids.get('categories', []))
        sub_id_set = set(s['id'] for s in sub_ids.get('subcategories', []))

        big_missing = 0
        sub_missing = 0
        invalid_big = 0
        invalid_sub = 0
        for r in records:
            bid = r.get('big_category_id')
            sid = r.get('subcategory_id')
            if not bid:
                big_missing += 1
            elif bid not in big_id_set:
                invalid_big += 1
                if invalid_big <= 3:
                    failures.append(f"❌ record {r.get('id')}  big_category_id={bid!r} 不在 category_ids.json 中")
            if not sid:
                sub_missing += 1
            elif sid not in sub_id_set:
                invalid_sub += 1
                if invalid_sub <= 3:
                    failures.append(f"❌ record {r.get('id')}  subcategory_id={sid!r} 不在 subcategory_ids.json 中")

            # failed_items 内嵌字段
            for fi in r.get('failed_items', []):
                if not fi.get('big_category_id'):
                    big_missing += 1
                if not fi.get('subcategory_id'):
                    sub_missing += 1
                # table_id 可为 None（数据源无表号），有值时校验
                tid = fi.get('table_id')
                if tid is not None and tid != '':
                    table_ids = json.load(open(os.path.join(root, 'data/table_ids.json'), encoding='utf-8'))
                    table_id_set = set(t['id'] for t in table_ids.get('tables', []))
                    if tid not in table_id_set:
                        invalid_big += 1

        if big_missing == 0 and invalid_big == 0:
            print(f"  ✅ big_category_id 全部 {len(records)} 条覆盖且合法")
        if sub_missing == 0 and invalid_sub == 0:
            print(f"  ✅ subcategory_id 全部 {len(records)} 条覆盖且合法")
        if big_missing:
            failures.append(f"❌ master.json  big_category_id 缺失 {big_missing} 处")
        if sub_missing:
            failures.append(f"❌ master.json  subcategory_id 缺失 {sub_missing} 处")
        if invalid_big:
            failures.append(f"❌ master.json  big_category_id 非法 {invalid_big} 处")
        if invalid_sub:
            failures.append(f"❌ master.json  subcategory_id 非法 {invalid_sub} 处")

        # 2.3 µ/μ 混用检查（仅扫描非 _raw 字段）
        print("\n[3] µ/μ 混用检查（仅非 _raw 字段）")
        def walk_strings(obj, path_parts=()):
            """递归生成所有 (path, value) 但排除 _raw 字段"""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(k.endswith(s) for s in ('_raw',)):
                        continue
                    yield from walk_strings(v, path_parts + (str(k),))
            elif isinstance(obj, list):
                for i, x in enumerate(obj):
                    yield from walk_strings(x, path_parts + (f'[{i}]',))
            elif isinstance(obj, str):
                yield (path_parts, obj)

        mixed_files = 0
        for rel in CORE_JSONS:
            path = os.path.join(root, rel)
            if not os.path.exists(path):
                continue
            try:
                d_check = json.load(open(path, encoding='utf-8'))
            except Exception:
                continue
            mixed_paths = []
            for p, v in walk_strings(d_check):
                if MU_MICRO in v and MU_GREEK in v:
                    mixed_paths.append('.'.join(p))
            if mixed_paths:
                mixed_files += 1
                failures.append(f"❌ {rel}  非 _raw 字段含 µ/μ 混用 {len(mixed_paths)} 处")
                for mp in mixed_paths[:5]:
                    failures.append(f"     - {mp}")
        if mixed_files == 0:
            print(f"  ✅ 所有 JSON 的非 _raw 字段无 µ/μ 混用")
        else:
            print(f"  ❌ {mixed_files} 个文件含混用")

        # 2.4 records 内部 failed_items 的混用检查（深度）
        # 规则：_raw 字段允许 Greek μ（存档原始公告）；非 _raw 字段必须都是 µ
        RAW_SUFFIXES = {'_raw'}
        def is_raw_field(name):
            return any(name.endswith(s) for s in RAW_SUFFIXES)

        deep_mixed = 0
        for r in records:
            for fi in r.get('failed_items', []):
                for fname, fval in fi.items():
                    if not isinstance(fval, str) or not fval:
                        continue
                    if is_raw_field(fname):
                        continue  # _raw 字段允许 Greek μ
                    if MU_MICRO in fval and MU_GREEK in fval:
                        deep_mixed += 1
                        if deep_mixed <= 3:
                            failures.append(f"❌ record {r.get('id')}  failed_items.{fname} 混用：{fval!r}")
            # fail_raw 也算非 raw 字段（虽然名字带 raw 但语义是"公告原文"，应统一）
            fr = r.get('fail_raw', '') or ''
            if fr and MU_MICRO in fr and MU_GREEK in fr:
                deep_mixed += 1
                if deep_mixed <= 3:
                    failures.append(f"❌ record {r.get('id')}  fail_raw 混用：{fr!r}")
        if deep_mixed > 0:
            failures.append(f"❌ master.json  failed_items / fail_raw 含 {deep_mixed} 条 µ/μ 混用")
        else:
            print(f"  ✅ master.json  failed_items / fail_raw 无 µ/μ 混用（_raw 存档字段除外）")

    # ============================================================
    # 4. 表号重复警告（gb_checklist_subcat.json）
    # 区分两类重复：
    #   (a) 同 table_no 在多个 big_category 出现 → 跨大类续编（已知 PDF 现象）
    #   (b) 同 table_no 在同一 big_category 多次出现 → 同大类续编
    # ============================================================
    print("\n[4] 表号续编警告")
    gbs_path = os.path.join(root, 'data/current_period/gb_checklist_subcat.json')
    table_ids_path = os.path.join(root, 'data/table_ids.json')
    if os.path.exists(gbs_path) and os.path.exists(table_ids_path):
        gbs = json.load(open(gbs_path, encoding='utf-8'))
        tids = json.load(open(table_ids_path, encoding='utf-8'))
        # table_id set 校验
        tid_set = set(t['id'] for t in tids.get('tables', []))

        # 按 (big, table_no) → list[sub_name]
        loc = {}
        for big, tables in gbs.get('categories', {}).items():
            if not isinstance(tables, list):
                continue
            for t in tables:
                if not isinstance(t, dict):
                    continue
                tno = t.get('table_no') or ''
                if not tno:
                    continue
                loc.setdefault(tno, {}).setdefault(big, []).append(t.get('name', ''))

        # 找重复：table_no 在多个 big 或同 big 多张
        cross = {tno: bd for tno, bd in loc.items() if len(bd) > 1}
        same = {}
        for tno, bd in loc.items():
            for big, subs in bd.items():
                if len(subs) > 1:
                    same.setdefault(tno, []).append((big, subs))
        if cross:
            for tno, bd in sorted(cross.items()):
                warnings.append(f"⚠️ 表号 {tno} 跨大类续编：{sorted(bd.keys())}")
                print(f"  ⚠️ 表号 {tno} 跨大类续编：{sorted(bd.keys())}")
        if same:
            for tno, groups in sorted(same.items()):
                warnings.append(f"⚠️ 表号 {tno} 同大类内多张：{groups}")
                print(f"  ⚠️ 表号 {tno} 同大类内多张：{groups}")
        if not cross and not same:
            print(f"  ✅ {len(loc)} 个表号，无重复")

        # table_ids.json 校验
        all_table_ids = [t['id'] for t in tids.get('tables', [])]
        if len(set(all_table_ids)) != len(all_table_ids):
            failures.append(f"❌ table_ids.json 含重复 id")
        else:
            print(f"  ✅ table_ids.json  {len(all_table_ids)} 条 id 唯一")
        # continuation_of 引用合法
        tid_set_global = set(all_table_ids)
        bad_refs = [t['id'] for t in tids.get('tables', []) if t.get('continuation_of') and t['continuation_of'] not in tid_set_global]
        if bad_refs:
            failures.append(f"❌ table_ids.json  {len(bad_refs)} 条 continuation_of 引用不存在")
        else:
            print(f"  ✅ table_ids.json  continuation_of 引用全部合法")

    # ============================================================
    # 汇总
    # ============================================================
    print("\n" + "=" * 60)
    print(f"汇总：失败 {len(failures)}  警告 {len(warnings)}")
    print("=" * 60)
    if failures:
        print("\n【失败项】")
        for f in failures:
            print(f"  {f}")
    if warnings:
        print("\n【警告项】")
        for w in warnings:
            print(f"  {w}")

    if failures:
        print(f"\n❌ 校验失败，{len(failures)} 项必须修复")
        sys.exit(1)
    if warnings and args.strict:
        print(f"\n❌ 严格模式下警告也视作失败")
        sys.exit(1)
    if warnings:
        print(f"\n⚠️ 仅警告，可发布（严格模式请加 --strict）")
    else:
        print(f"\n✅ 全部通过，可以发布")
    sys.exit(0)


if __name__ == '__main__':
    main()