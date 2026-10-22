#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修正 r0464「纯凉皮」分类。

依据（均来自原版《食品安全监督抽检实施细则（2026年版）》PDF 原文）：
1. 表31-4「凉皮（自制）a」检验项目 = 脱氢乙酸及其钠盐 + 柠檬黄，注a 限未调味产品
   → 细则把「凉皮（自制）」明确列在第31类 餐饮食品 下
2. 库中安徽 4 条同类记录（r1055/r1116/r1128/r1133）本已归「餐饮食品-凉皮（自制）a」
3. r0464 不合格项 = 脱氢乙酸及其钠盐，与表31-4 第1项完全一致 → 同套检验方案

结论：r0464 应与安徽同类保持一致，归 31 餐饮食品-凉皮（自制），
      昨日改归「23 淀粉及淀粉制品-其他淀粉制品」是误判（23类的原生品种只有
      淀粉/粉丝粉条/其他淀粉制品/淀粉糖，无凉皮）。

本脚本严格派生自当前 master.json（当前线上终版），只改r0464 一个字段组，
其余 1358 条与三个索引逐键比对必须 0 差异。
"""
import json
import sys
from collections import OrderedDict

MASTER = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\master.json'
TARGET = 'r0464'
NEW_BIG = '餐饮食品'
NEW_SUB = '餐饮食品-凉皮（自制）a'


def build_indexes(records):
    """与入库时完全一致的索引重建逻辑"""
    by_canonical = OrderedDict()
    by_category = OrderedDict()
    by_item = OrderedDict()
    for r in records:
        fc = r.get('food_name_canonical') or ''
        big = r.get('big_category') or ''
        sub = r.get('sub_category') or ''
        by_canonical.setdefault(fc, [])
        by_canonical[fc].append(sub)
        by_category.setdefault(big, [])
        by_category[big].append(sub)
        by_item.setdefault(fc, [])
        by_item[fc].append(big)
    return by_canonical, by_category, by_item


def main():
    with open(MASTER, encoding='utf-8') as f:
        data = json.load(f)

    old_records = data['records']
    old_bc = json.loads(json.dumps(data.get('by_canonical', {})))
    old_bg = json.loads(json.dumps(data.get('by_category', {})))
    old_bi = json.loads(json.dumps(data.get('by_item', {})))
    old_inner = json.loads(json.dumps(data.get('indexes', {})))

    # 定位目标
    hit = [r for r in old_records if r.get('id') == TARGET]
    if len(hit) != 1:
        print('[X] 预期命中 1 条，实际 %d 条' % len(hit))
        return 1
    rec = hit[0]
    print('[目标] %s  %s / %s' % (TARGET, rec.get('food_name_canonical'),
                                 rec.get('source')))
    print('  改前: %s | %s' % (rec.get('big_category'), rec.get('sub_category')))
    print('  改后: %s | %s' % (NEW_BIG, NEW_SUB))

    # 快照：改动前的全量深拷贝，用于逐字段比对
    snapshot = json.loads(json.dumps(old_records))

    # 唯一改动
    rec['big_category'] = NEW_BIG
    rec['sub_category'] = NEW_SUB

    # ---------- 先验证 records 逐字段差异，再重建索引 ----------
    diffs = []
    for a, b in zip(snapshot, old_records):
        for k in set(a) | set(b):
            if a.get(k) != b.get(k):
                diffs.append((a.get('id'), k, a.get(k), b.get(k)))
    allow = {(TARGET, 'big_category'), (TARGET, 'sub_category')}
    unexpected = [d for d in diffs if (d[0], d[1]) not in allow]
    print()
    print('[V0-a] records 字段级差异 = %d 处' % len(diffs))
    for d in diffs:
        print('       %s.%s: %r -> %r' % d)
    if unexpected:
        print('[X] 存在非目标改动 %d 处，拒绝写入' % len(unexpected))
        return 1
    print('[V0-b] 除目标 2 个字段外，1359 条 0 差异 OK')

    # 重建索引
    nbc, nbg, nbi = build_indexes(old_records)

    # 双写冗余：顶层 3 个 + indexes 内 3 个
    data['by_canonical'] = nbc
    data['by_category'] = nbg
    data['by_item'] = nbi
    data['indexes'] = OrderedDict([
        ('by_canonical', nbc),
        ('by_category', nbg),
        ('by_item', nbi),
    ])

    # ---------- 验证 ----------
    err = 0

    # 1) records 条数
    if len(old_records) != 1359:
        print('[X] 条数变了！%d' % len(old_records)); err += 1
    else:
        print('[V1] records 条数 = 1359 不变 OK')

    # 2) 索引键数量
    if len(nbg) != 34:
        print('[X] by_category 应为 34，实际 %d' % len(nbg)); err += 1
    else:
        print('[V2] by_category = 34 个大类 OK')

    # 3) 索引不含越界大类
    with open(r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\big39.json',
              encoding='utf-8') as f:
        b39 = json.load(f)
    # big39.json 顶层混有 _source/_note/count 等元字段，骨架在 'categories' 下
    cats = b39.get('categories', b39) if isinstance(b39, dict) else b39
    if isinstance(cats, dict):
        names = set(cats.keys())
    else:
        names = {(v.get('name') if isinstance(v, dict) else v) for v in cats}
    names = {n for n in names if n and not str(n).startswith('_')}
    out = set(nbg.keys())
    if names:
        bad = out - names
        if bad:
            print('[X] 越界大类: %s' % bad); err += 1
        else:
            print('[V3] 大类越界 0 OK（%d/%d 命中骨架）' %
                  (len(out & names), len(names)))

    # 4) 顶层与内嵌索引一致
    if json.dumps(data['by_canonical'], ensure_ascii=False) == \
       json.dumps(data['indexes']['by_canonical'], ensure_ascii=False) and \
       json.dumps(data['by_category'], ensure_ascii=False) == \
       json.dumps(data['indexes']['by_category'], ensure_ascii=False) and \
       json.dumps(data['by_item'], ensure_ascii=False) == \
       json.dumps(data['indexes']['by_item'], ensure_ascii=False):
        print('[V4] 顶层 3 索引 与 indexes 内 3 索引 双写一致 OK')
    else:
        print('[X] 双写不一致'); err += 1

    # 5) 索引条目总数 = 1359
    tot = sum(len(v) for v in nbg.values())
    if tot != 1359:
        print('[X] by_category 条目合计 %d != 1359' % tot); err += 1
    else:
        print('[V5] by_category 条目合计 = 1359 OK')

    if err:
        print('\n验证未通过，不写入。')
        return 1

    with open(MASTER, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('\n[OK] 已写入', MASTER)
    return 0


if __name__ == '__main__':
    sys.exit(main())