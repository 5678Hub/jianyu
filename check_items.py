#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
不合格项 × 归类 反证校验（硬判据版）

原理：不合格项来自该大类的检验项目表。
若某条记录的不合格项**完全不在**其 big_category 对应的检验项目集里，
则该记录归类可疑（可能是大类错了，或省级加检项）。

数据源：
  data/xize_items.json  ← 从原版细则 PDF 的「表NN-N XXX检验项目」抽出的
                           各大类实际检验项目（1029 项/ 35 大类）

输出：
  · 高置信可疑（不合格项 100% 不在本大类项目集）
  · 部分可疑（部分项目不在，常见于省级加检）
  · 覆盖率分布
"""
import json
import re
from collections import Counter, defaultdict

BASE = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data'


def norm(s):
    """归一化项目名：去序号、去尾注字母、去空白、去标点、去Unicode下标"""
    s = (s or '').strip()
    # Unicode 下标/上标统一化（₁ ₂ ₃ 等）
    s = (s.replace('₁', '1').replace('₂', '2').replace('₃', '3')
          .replace('₄', '4').replace('₅', '5').replace('₆', '6')
          .replace('₇', '7').replace('₈', '8').replace('₉', '9')
          .replace('₀', '0'))
    # 全角→半角
    s = s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    # 空格含不间断空格
    s = re.sub(r'[\s 　]+', '', s)
    # 去表格残留序号
    s = re.sub(r'^\d{1,3}(?=[一-龥])', '', s)
    # 去尾注字母
    s = re.sub(r'[a-z]+$', '', s)
    # 去括号内容
    s = re.sub(r'[（(].*?[)）]', '', s)
    s = re.sub(r'[、，,。·/%％\-]', '', s)
    return s.strip()


def canon(s):
    """进一步归一：只保留中文+数字，抹平计量说明与组合符号。

    「黄曲霉毒素B1」→ 黄曲霉毒素B1
    「土霉素/金霉素/四环素（组合含量）」→ 土霉素金霉素四环素
    """
    s = norm(s)
    s = re.sub(r'^[（(].*?[)）]', '', s)
    # 组合项：整条作为一个不可分单位，另存单字符形式
    return s


def expand(s):
    """把细则的组合项展开成可匹配子集。

    例：「合成着色剂（柠檬黄、日落黄、胭脂红、苋菜红、亮蓝）」→ 展开出
        {'合成着色剂', '柠檬黄', '日落黄', '胭脂红', '苋菜红', '亮蓝'}
    这样库里单独记的「柠檬黄」也能匹配上。
    """
    s = (s or '').strip()
    m = re.match(r'^(.*?)[（(]([^)）]*)[)）]\s*[a-z]?$', s)
    if not m:
        return {norm(s)}
    head = m.group(1)
    subs = [x for x in re.split(r'[、,，]', m.group(2)) if x.strip()]
    out = {norm(head)}
    for x in subs:
        out.add(norm(x))
    return {x for x in out if x}


def loose(s):
    """更宽松：只保留项目主体中文/数字"""
    s = re.sub(r'[（(].*?[)）]', '', s or '')
    s = re.sub(r'\s+', '', s)
    return s


def main():
    m = json.load(open(BASE + r'\master.json', encoding='utf-8'))
    xz = json.load(open(BASE + r'\xize_variants.json', encoding='utf-8'))
    items = json.load(open(BASE + r'\xize_items.json', encoding='utf-8'))
    recs = m['records']

    # 大类名 -> 序号
    name2no = {v['name']: int(k) for k, v in xz.items()}
    # 大类名 -> 归一化项目集（组合项已展开）
    big2items = {}
    for k, lst in items.items():
        no = int(k)
        nm = xz.get(str(no), {}).get('name')
        if not nm:
            continue
        s = set()
        for x in lst:
            s |= expand(x)
        big2items[nm] = s

    print('=' * 74)
    print('不合格项 × 归类 反证校验')
    print('细则检验项目集：%d 个大类 / %d 个项目' %
          (len(big2items), sum(len(v) for v in big2items.values())))
    print('=' * 74)

    # 全库所有出现过的不合格项
    all_items = set()
    for r in recs:
        for x in (r.get('failed_items') or []):
            n = norm(x.get('item'))
            if n:
                all_items.add(n)
    covered = set()
    for s in big2items.values():
        covered |= s
    unc = all_items - covered
    print()
    print('库里出现的不合格项 %d 种，其中细则项目集未收录 %d 种 (%.1f%%)' %
          (len(all_items), len(unc), len(unc) / max(1, len(all_items)) * 100))
    print('（未收录的通常是省级加检/细则 PDF 抽取漏项，不作为可疑依据）')
    print('  未收录样例: %s' % '、'.join(sorted(unc)[:20]))

    # 逐条校验
    hard, soft = [], []
    for r in recs:
        bc = r.get('big_category')
        allowed = big2items.get(bc)
        if not allowed:
            continue
        fis = [x.get('item') for x in (r.get('failed_items') or []) if x.get('item')]
        if not fis:
            continue
        miss = []
        for it in fis:
            n = norm(it)
            if n in allowed:
                continue
            # 宽松包含
            if any(n and (n in a or a in n) for a in allowed):
                continue
            miss.append(it)
        if not miss:
            continue
        rate = 1 - len(miss) / len(fis)
        rec = (r, miss, rate)
        if rate == 0:
            hard.append(rec)
        else:
            soft.append(rec)

    total = len(recs)
    print()
    print('-' * 74)
    print('【高置信可疑】不合格项 100%% 不在本大类检验项目集 = %d 条 (%.2f%%)'
          % (len(hard), len(hard) / total * 100))
    print('-' * 74)
    g = defaultdict(list)
    for r, miss, _ in hard:
        g[r.get('big_category')].append((r, miss))
    for k in sorted(g, key=lambda x: -len(g[x])):
        print()
        print('  ■ %s  %d 条' % (k, len(g[k])))
        for r, miss in g[k][:8]:
            fi = '、'.join(str(x.get('item')) for x in r['failed_items'])
            print('     %-8s %-4s %-22s | 不合格: %s' %
                  (r['id'], r.get('source'),
                   str(r.get('food_name_canonical'))[:20], fi[:60]))
        if len(g[k]) > 8:
            print('     ... 另 %d 条' % (len(g[k]) - 8))

    print()
    print('-' * 74)
    print('【部分可疑】部分项目不在本大类项目集 = %d 条 (%.2f%%)  ← 多为省级加检，暂不动'
          % (len(soft), len(soft) / total * 100))

    # 汇总
    print()
    print('=' * 74)
    print('结论')
    print('  高置信可疑%d / %d = %.2f%% → 反推「大类归对率」≈ %.2f%%'
          % (len(hard), total, len(hard) / total * 100,
             (total - len(hard)) / total * 100))
    print('  （高置信可疑中仍有一部分是省级加检项目导致的误报，需逐条人工确认）')


if __name__ == '__main__':
    main()