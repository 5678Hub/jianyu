#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用原版细则品种表反查库中1359 条记录：
1. 库中每个品种是否在细则里有对应
2. 已知的边界案例（菠萝/丑橘/红虾/凉皮/北豆）逐一核实
3. 找出「库里用了但细则表标题没抽到」的品种，人工判断是细则外还是抽取漏了
"""
import json
import re
from collections import Counter, defaultdict

XZ = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\xize_variants.json'
MASTER = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\master.json'


def norm(s):
    """归一化：去空白/括号/标点，便于比对"""
    if not s:
        return ''
    s = re.sub(r'[（(].*?[)）]', '', s)
    s = re.sub(r'[\s、,，。/·]', '', s)
    return s


def main():
    xz = json.load(open(XZ, encoding='utf-8'))
    m = json.load(open(MASTER, encoding='utf-8'))
    recs = m['records']

    # 细则品种索引：大类 -> 品种集
    big2vars = {}
    for k, v in xz.items():
        vs = set(norm(x) for x in v['variants'] if x)
        for sub, items in v['sub'].items():
            for it in items:
                vs.add(norm(it))
        big2vars[int(k)] = (v['name'], vs)

    total_vars = sum(len(vs) for _, vs in big2vars.values())
    print('细则品种库：%d 个大类 / %d 个品种（含子表）\n' % (len(big2vars), total_vars))

    # 库中所有品种
    lib = Counter()
    lib_big = defaultdict(set)
    for r in recs:
        fn = norm(r.get('food_name_canonical') or r.get('food_name_raw'))
        if not fn:
            continue
        lib[fn] += 1
        lib_big[fn].add(r.get('big_category'))

    print('库中不重复品种数 = %d\n' % len(lib))

    # 逐个大类核对
    print('%-4s %-18s %6s %8s %8s' % ('#', '大类', '库中条', '细则品种', '命中率'))
    print('-' * 52)
    miss_by_big = defaultdict(list)
    for no in range(1, 40):
        name, varset = big2vars[no]
        # 库中归属该大类的记录
        n = sum(1 for r in recs if r.get('big_category') == name)
        if n == 0:
            continue
        hit, miss = [], []
        for fn, cnt in lib.items():
            if name in lib_big[fn]:
                if fn in varset:
                    hit.append(fn)
                else:
                    miss.append((fn, cnt))
        rate = '%5.0f%%' % (100.0 * len(hit) / max(1, len(hit) + len(miss)))
        print('%-4d %-18s %6d %8d %8s' % (no, name, n, len(varset), rate))
        for fn, cnt in sorted(miss, key=lambda x: -x[1]):
            miss_by_big[name].append((fn, cnt))

    print('\n' + '=' * 70)
    print('【库中有、但细则品种表未列出的品种】共 %d 个' % len(miss_by_big))
    print('=' * 70)
    for name in sorted(miss_by_big):
        items = miss_by_big[name]
        tot = sum(c for _, c in items)
        print('\n■ %s（%d 条，%d 个品种）' % (name, tot, len(items)))
        for fn, cnt in sorted(items, key=lambda x: -x[1]):
            print('    %-22s %3d 条' % (fn, cnt))

    # 已知边界案例
    print('\n' + '=' * 70)
    print('【已知边界案例核实】')
    print('=' * 70)
    cases = ['菠萝', '凤梨', '丑桔', '丑橘', '红虾', '凉皮', '北豆', '南极北豆']
    for c in cases:
        key = norm(c)
        where = [no for no, (nm, vs) in big2vars.items() if key in vs]
        cnt = lib.get(key, 0)
        print('  %-8s 细则品种表: %-18s 库中 %d 条' % (
            c, ('第%d类 %s' % (where[0], big2vars[where[0]][0])) if where else '【未列】', cnt))


if __name__ == '__main__':
    main()