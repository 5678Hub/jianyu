#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从原版《食品安全监督抽检实施细则（2026年版）》PDF 抽取 39 大类完整品种清单。

策略：
1. 一级大类：从目录页正则抽「中文数字、名称」+页码（页码允许「错误」）
2. 二级/品种：从「表NN-N 品种名检验项目」标题抽——细则里每张检验项目表
   对应一个具体品种，标题即品种名
3. 部分大类（如36 水果类）另有「表36-1 具体抽检XX品种及所属XX分类」的品种归属表，
   单独抽，形成 big->sub->item 三层
"""
import fitz
import re
import json
import sys
from collections import OrderedDict

PDF = r'E:\Mrlee\食品安全监测抽检实施细则（2026年版）.pdf'
OUT = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data\xize_variants.json'

CN = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
      '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
      '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八',
      '二十九', '三十', '三十一', '三十二', '三十三', '三十四', '三十五', '三十六',
      '三十七', '三十八', '三十九']

# 目录里出现的一级标题
# 正文真实排版（已核实 repr）：
#   '1\n一、粮食加工品 \n1 小麦粉 \n1.1 适用范围 \n...'
# 即：一级标题后紧跟「N 二级标题」，再跟「1.1 适用范围」
HEAD = re.compile(r'([一二三四五六七八九十]{1,3})、([^\n]{2,18}?)\s*\n\s*\d{0,3}\s*[^\n]{0,20}?\n\s*\d\.\d\s*适用范围')


def chapter_page_bounds(doc, full):
    """逐页顺序扫描定位每个一级大类正文的起始 PDF 页。

    不依赖正则匹配「一、XXX + 二级标题 + 1.1适用范围」这种易碎组合，
    而是全文顺序流式解析：一旦出现「一、XXX」即为该类起点，直到下一个起点。
    返回 [(起始PDF页, 章节序号, 类名)]
    """
    marks = []
    for i in range(4, doc.page_count):          # 正文从 PDF 第5页起
        t = doc[i].get_text()
        # ⚠ 两种排版都要匹配（已核实原文 repr）：
        #   A) '三十三、畜禽肉及副产品 \n1 适用范围 \n...'← 该类无二级标题层
        #   B) '一、粮食加工品 \n1 小麦粉 \n1.1 适用范围 \n...'  ← 有二级标题层
        for m in re.finditer(r'([一二三四五六七八九十]{1,3})、([^\n]{2,18})', t):
            cn, name = m.group(1), m.group(2).strip()
            if cn in CN:
                marks.append((i + 1, CN.index(cn) + 1, name))
    # 同序号只保留首次出现
    seen, out = set(), []
    for pg, no, nm in marks:
        if no not in seen:
            seen.add(no)
            out.append((pg, no, nm))
    return out


def offset_to_page(full, offset, doc, prefix=None):
    """把全文字符偏移映射到 PDF 页号（用累积长度前缀表，二分）"""
    if prefix is None:
        prefix = []
        cum = 0
        for i in range(doc.page_count):
            prefix.append(cum)
            cum += len(doc[i].get_text())
        prefix.append(cum)
    import bisect
    return bisect.bisect_right(prefix, offset)


def page_to_big(page, bounds):
    """PDF 页号 -> 章节序号（bounds 为按页排序的 (页, 序号, 名)）"""
    cur = 0
    for pg, no, nm in bounds:
        if page >= pg:
            cur = no
        else:
            break
    return cur


def main():
    doc = fitz.open(PDF)
    full = ''.join(doc[i].get_text() for i in range(doc.page_count))
    toc = ''.join(doc[i].get_text() for i in range(1, 5))

    # ---------- 1. 一级大类 ----------
    # 页码允许: 数字 或「错误」（Word 书签丢失，如「三十二、食品添加剂（暂无）」）
    pat = re.compile(r'([一二三四五六七八九十]{1,3})、\s*([^\n\.]{2,25}?)\s*(?:\.+|\s)\s*(\d+|错误)')
    order_map = {}
    for m in pat.finditer(toc):
        cn = m.group(1)
        name = m.group(2).strip().replace('（暂无）', '')
        if cn in CN and cn not in order_map:
            order_map[cn] = name

    big = OrderedDict()
    for i, cn in enumerate(CN, 1):
        if cn in order_map:
            big[str(i)] = {
                'no': i,
                'cn': cn,
                'name': order_map[cn],
                'variants': [],       # 表标题抽到的品种
                'sub': OrderedDict()  # 品种归属表抽到的子类
            }
    print('[1] 一级大类 %d 个' % len(big))

    # ---------- 2. 表标题里的品种名 ----------
    # 形如「表1-1 小麦粉检验项目」「表 10-1 冷冻饮品检验项目」（注意「表」后可能有空格）
    # 二级序号可>9（如 表33-71）
    #
    # ⚠ 原版PDF 的表号缺陷（已核实，非抽取错误）：
    #   ·「三十五、水产品」的表被误编为 33-44 海水鱼、33-8 其他水产品（在PDF 361-390页）
    #   ·「三十七、鲜蛋」的表被误编为 33-71 鸡蛋、33-72 其他禽蛋（在PDF 391页后）
    #   ·「三十二、食品添加剂」目录标注「（暂无）」，无正文
    # 修正策略：先按页序切出每章的 PDF 页区间，再按区间归属，不信任表号前缀
    page_bounds = chapter_page_bounds(doc, full)
    _pref, _c = [], 0
    for i in range(doc.page_count):
        _pref.append(_c)
        _c += len(doc[i].get_text())
    _pref.append(_c)
    print('[0] 章节起始页: %s' % ', '.join('%d@p%d' % (no, pg) for pg, no, nm in page_bounds))
    got = {no for _, no, _ in page_bounds}
    missing_ch = [i for i in range(1, 40) if i not in got]
    if missing_ch:
        print('    未定位到正文章节的序号: %s' % missing_ch)

    tab_pat = re.compile(r'表\s*(\d{1,2})\s*-\s*(\d{1,3})\s+([^\n]{2,40}?)检验项目')
    for m in tab_pat.finditer(full):
        b_tab = int(m.group(1))
        title = re.sub(r'\s+', '', re.sub(r'[a-z]$', '', m.group(3).strip()))
        page = offset_to_page(full, m.start(), doc, _pref)
        b_page = page_to_big(page, page_bounds)
        # 表号与页面章节一致才用表号，否则以页面章节为准
        b = b_tab if b_tab == b_page else b_page
        key = str(b)
        if key in big and title:
            big[key]['variants'].append(title)

    # 去重保序
    for k, v in big.items():
        seen = set()
        uniq = []
        for t in v['variants']:
            if t not in seen:
                seen.add(t)
                uniq.append(t)
        v['variants'] = uniq
    total = sum(len(v['variants']) for v in big.values())
    print('[2] 表标题品种 %d 个' % total)

    # ---------- 3. 品种归属表（亚类归属）----------
    # 形如「表36-1 具体抽检水果品种及所属水果分类」，正文是「序号 品种 亚类」三列
    sub_pat = re.compile(
        r'表(\d{1,2})-1\s*具体抽检([^\n]{2,20}?)品种及所属([^\n]{2,20}?分类)')
    for m in sub_pat.finditer(full):
        b = int(m.group(1))
        if str(b) not in big:
            continue
        start = m.end()
        seg = full[start:start + 3000]
        # 逐行抽取：序号 品种 分类
        rows = re.findall(
            r'(\d{1,2})\s*\n\s*([^\n\d]{1,15}?)\s*\n\s*([^\n]{2,14}?(?:类|水果|干|制品|食品))',
            seg)
        for no, item, sub in rows:
            item = item.strip()
            sub = sub.strip()
            if item and sub:
                big[str(b)]['sub'].setdefault(sub, [])
                if item not in big[str(b)]['sub'][sub]:
                    big[str(b)]['sub'][sub].append(item)

    nsub = sum(len(v['sub']) for v in big.values())
    nitem = sum(len(x) for v in big.values() for x in v['sub'].values())
    print('[3] 归属表：%d 个子类 / %d 个品种' % (nsub, nitem))

    # ---------- 输出 ----------
    out = OrderedDict()
    for k, v in big.items():
        out[k] = OrderedDict([
            ('no', v['no']),
            ('cn', v['cn']),
            ('name', v['name']),
            ('variant_count', len(v['variants'])),
            ('variants', v['variants']),
            ('sub', OrderedDict(v['sub'])),
        ])
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('[OK] 已写入', OUT)

    print()
    print('%-4s %-18s %6s %6s' % ('#', '大类', '品种', '子类'))
    print('-' * 46)
    for k, v in out.items():
        print('%-4s %-18s %6d %6d' % (k, v['name'], v['variant_count'], len(v['sub'])))


if __name__ == '__main__':
    main()