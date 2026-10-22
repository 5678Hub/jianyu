#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从原版细则 PDF 抽取各大类「检验项目」全集（v4）

v4 修正 v3 的两个问题：
  1) v3 用「下一个表标题」切片，导致尾部表把下一个章节的内容吞进来
     （33类畜禽肉里混进了 34类蔬菜的「豆芽豆芽」「叶菜类蔬菜」等）
  2) v3 只展开括号，不拆药名并列
     （「土霉素/金霉素/四环素（组合含量）」匹配不上库里的「金霉素」）

v4 做法：
  · 采集时记录每个项目名在全文中的字符偏移
  · 归属一律按「字符偏移落在哪一章」判定，完全不信表号
  · 展开时既拆括号，也拆药名并列
"""
import bisect
import fitz
import json
import re
from collections import defaultdict

PDF = r'E:\Mrlee\食品安全监测抽检实施细则（2026年版）.pdf'
OUT = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\xize_items.json'
VARIANTS = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\xize_variants.json'

CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
      '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八',
      '十九', '二十', '二十一', '二十二', '二十三', '二十四', '二十五',
      '二十六', '二十七', '二十八', '二十九', '三十', '三十一', '三十二',
      '三十三', '三十四', '三十五', '三十六', '三十七', '三十八', '三十九']

STD_LINE = re.compile(
    r'^(?:GB|SC|NY|SN|JJF|BJS|DBS|Q/|QB/|SB/T|T/|参照|相关的产品|'
    r'整顿办|农业农村部|国家食品|产品明示标准和质量要求|GB\s|T\s*1)')
NAME_OK = re.compile(r'[一-龥]')
JUNK = [r'^序号检验项目依据法律法规或标准检测方法', r'^序号', r'^检验项目',
        r'^依据法律法规或标准', r'^检测方法']

DRUGS = ['土霉素', '金霉素', '四环素', '氯霉素', '恩诺沙星', '诺氟沙星',
         '氧氟沙星', '洛美沙星', '培氟沙星', '多西环素', '替米考星',
         '林可霉素', '大环内酯', '磺胺类', '喹乙醇', '氯丙嗪',
         '氟苯尼考', '双氯芬酸', '甲硝唑', '甲氧苄啶', '阿莫西林',
         '氟丙嗪', '苯巴比妥', '地西泮', '氯硝西泮', '苯并芘']


def clean(s):
    s = (s or '').strip()
    for a, b in [('₁', '1'), ('₂', '2'), ('₃', '3'), ('₄', '4'), ('₅', '5'),
                 ('₆', '6'), ('₇', '7'), ('₈', '8'), ('₉', '9'), ('₀', '0')]:
        s = s.replace(a, b)
    s = s.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    s = re.sub(r'[\s 　]+', '', s)
    s = re.sub(r'^\d{1,3}(?=[一-龥])', '', s)
    for p in JUNK:
        s = re.sub(p, '', s)
    s = re.sub(r'[a-z]{1,3}$', '', s)
    s = re.sub(r'[，,。；;：:、/％%\.\-]', '', s)
    s = re.sub(r'[（(]\s*[)）]', '', s)
    return s.strip()


def expand(s):
    """组合项展开：括号子项 + 药名并列"""
    s = (s or '').strip()
    out = {clean(s)}
    for m in re.finditer(r'（([^)）]*)）', s):
        for x in re.split(r'[、,，]', m.group(1)):
            x = clean(x)
            if x and NAME_OK.search(x):
                out.add(x)
    for kw in DRUGS:
        if kw in s:
            out.add(kw)
    return {x for x in out if x and NAME_OK.search(x)}


def main():
    doc = fitz.open(PDF)
    pages = [doc[i].get_text() for i in range(doc.page_count)]
    full = ''.join(pages)

    # ---- 字符偏移前缀表（一次扫描，后续二分查页）----
    pref, c = [], 0
    for t in pages:
        pref.append(c)
        c += len(t)
    pref.append(c)

    def off_to_page(off):
        return bisect.bisect_right(pref, off)

    # ---- 一级大类正文起始偏移（逐页扫描，遇「X、YYY」换类）----
    chap = {}       # 序号 -> 起始字符偏移
    for i in range(4, doc.page_count):
        base = pref[i]
        for m in re.finditer(r'([一二三四五六七八九十]{1,3})、([^\n]{2,18})',
                             pages[i]):
            cn = m.group(1)
            if cn in CN:
                no = CN.index(cn) + 1
                if no not in chap:
                    chap[no] = base + m.start()
    print('定位一级大类正文 %d 个' % len(chap))
    chaps = sorted(chap.items(), key=lambda x: x[1])
    ch_offs = [o for _, o in chaps]

    def big_at(off):
        idx = bisect.bisect_right(ch_offs, off) - 1
        return chaps[idx][0] if idx >= 0 else 1

    # ---- 定位所有检验项目表标题 ----
    heads = [(m.start(), m.end(), int(m.group(1)), re.sub(r'\s+', '', m.group(3)))
             for m in re.finditer(
                 r'表\s*(\d{1,2})\s*-\s*(\d{1,3})\s+([^\n]{0,30}?)检验项目', full)]
    # ⚠ 排除品种归属表（表36-1、34-1 这类标题里不含「检验项目」的表，
    #   但会被上面的宽松正则从表体里误抓）：标题含这些词的一律剔除
    NOT_ITEM = re.compile(r'所属.{0,6}分类|品种及所属|具体抽检品种|品种分类')
    before = len(heads)
    heads = [h for h in heads if not NOT_ITEM.search(h[3])]
    # 标题里带「见表」的说明句剔除
    heads = [h for h in heads if '见表' not in h[3]]
    print('定位检验项目表标题 %d 个（剔除非检验表 %d 个）'
          % (len(heads), before - len(heads)))

    collected = []# (偏移, 大类, 项目名)
    for k, (pos, epos, b_tab, title) in enumerate(heads):
        this_big = big_at(pos)
        # ⭐ 硬边界：切片不得越过本章结束（下一个一级标题）
        #   这是v3 把34类蔬菜表吸进33类的根因
        chap_end = len(full)
        for no, off in chaps:
            if off > pos:
                chap_end = off
                break
        nxt = heads[k + 1][0] if k + 1 < len(heads) else min(len(full), pos + 2500)
        nxt = min(nxt, chap_end)
        body = full[epos:nxt]
        buf, buf_start = [], None

        def flush(at):
            if not buf:
                return
            name = clean(''.join(buf))
            if 2 <= len(name) <= 25 and NAME_OK.search(name):
                collected.append((at if at is not None else buf_start,
                                  this_big, name))
            buf.clear()

        for ln in body.split('\n'):
            s = ln.strip()
            if not s:
                continue
            if STD_LINE.match(s) or re.fullmatch(r'\d{1,3}', s) \
                    or re.match(r'^注[：:]?[a-z]?$', s) \
                    or re.match(r'^[a-z][.．]', s):
                flush(epos)
                continue
            if buf_start is None:
                buf_start = pos
            buf.append(s)
            if sum(len(x) for x in buf) > 60:      # 误吞注脚
                buf.clear()
                buf_start = None
        flush(epos)

    # ---- 归属 + 展开 ----
    final = defaultdict(set)
    tab_moved = 0
    for off, b_tab_big, name in collected:
        real = big_at(off)
        if real != b_tab_big:
            tab_moved += 1
        final[real] |= expand(name)
    print('（按字符偏移修正大类归属 %d/%d 项）' % (tab_moved, len(collected)))

    print('覆盖大类 %d 个 / 展开后项目 %d 项\n' %
          (len(final), sum(len(v) for v in final.values())))
    xz = json.load(open(VARIANTS, encoding='utf-8'))
    for b in sorted(final):
        print('  第%2d类 %-20s %3d 项' %
              (b, xz.get(str(b), {}).get('name', '?%d' % b), len(final[b])))

    json.dump({str(k): sorted(v) for k, v in final.items()},
              open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n已存 %s' % OUT)

    print()
    print('=== 校验 ===')
    checks = [('33', ['金霉素', '氯霉素', '镉（以Cd计）']),
              ('34', ['苄基腺嘌呤（6BA）', '乙酰甲胺磷', '铅（以Pb计）']),
              ('31', ['菌落总数', '大肠菌群', '铅（以Pb计）']),
              ('36', ['二氧化硫残留量']),
              ('23', ['菌落总数', '霉菌和酵母']),
              ('28', ['锌', '硒']),
              ('6', ['电导率', '苋菜红']),
              ('21', ['不溶于水杂质']),
              ('3', ['总氮（以N计）'])]
    for b, tests in checks:
        s = final.get(int(b), set())
        print('  第%s类 %s:' % (b, xz.get(b, {}).get('name', '?')))
        for t in tests:
            print('     %-22s %s' % (t, t in s))
    # 反向：33 类不该再有蔬菜词
    v = final.get(33, set())
    leak = [x for x in v if '叶菜类蔬菜' in x or '豆芽' in x or '茄果' in x]
    print()
    print('  33类是否残留蔬菜类污染:', leak if leak else '无 ✓')


if __name__ == '__main__':
    main()