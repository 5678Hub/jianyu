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
    # ============================================================
    print("\n[4] 表号重复警告")
    gbs_path = os.path.join(root, 'data/current_period/gb_checklist_subcat.json')
    if os.path.exists(gbs_path):
        gbs = json.load(open(gbs_path, encoding='utf-8'))
        table_to_cats = {}
        for big, tables in gbs.get('categories', {}).items():
            if not isinstance(tables, list):
                continue
            for t in tables:
                if not isinstance(t, dict):
                    continue
                tno = t.get('table_no') or ''
                if tno:
                    table_to_cats.setdefault(tno, set()).add(big)
        dup = {k: v for k, v in table_to_cats.items() if len(v) > 1}
        if dup:
            for tno, cats in dup.items():
                warnings.append(f"⚠️ 表号 {tno} 跨大类续编：{sorted(cats)}")
                print(f"  ⚠️ 表号 {tno} 跨大类续编：{sorted(cats)}")
        else:
            print(f"  ✅ {len(table_to_cats)} 个表号，无重复")

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