#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分层命中率评估 v2

问题背景：单纯用"品种名精确相等"对细则品种表匹配，命中率只有 23%，
但这不代表数据错—— 因为：
  1) 细则表34-1 写的是「葱」「姜」，库中写「大葱」「生姜」→ 同一物种
  2) 细则表36-1 写「柑、橘」，库中写「丑桔」「贡桔」
  3) 细则写典型抽检品种，库中大量是商品名（"武大煎饼""贾寨豆干五香味"）

因此建立 SYN 映射表，把库中商品名映射到细则品种，再算命中率。

三个层级：
  L1 大类合规 = big_category ∈ 39 骨架   （铁律，必须 100%）
  L2 品类合理 = 品种可映射到细则品种     （含同义词/商品名）
  L3 细则原生 = 品种名精确等于细则品种   （最严，仅参考）

异常检测：
  A 归类冲突   B 非食品（餐饮具）   C 空骨架   D sub 前缀不一致
"""
import json
import re
from collections import Counter, defaultdict

BASE = r'D:\Apps\Tencent\.workbuddy\tmp\jy_deploy\data'

# ---- 库中商品名 → 细则品种 的映射（依据：同义/上位/商品牌归属）----
SYN = {
    # 蔬菜：细则写「葱」「姜」，库中写细分名
    '大葱': '葱', '小葱': '葱', '香葱': '葱', '大葱（自产）': '葱',
    '生姜': '姜', '老姜': '姜', '子姜': '姜', '嫩姜': '姜', '姜片': '姜',
    '白萝卜': '萝卜', '胡萝卜': '萝卜',
    '小白菜': '普通白菜（小白菜、小油菜、青菜）',
    '上海青': '普通白菜（小白菜、小油菜、青菜）',
    '油菜': '普通白菜（小白菜、小油菜、青菜）',
    '青菜': '普通白菜（小白菜、小油菜、青菜）',
    '荷兰豆': '食荚豌豆', '甜豆': '食荚豌豆',
    '四季豆': '菜豆', '芸豆': '菜豆', '白芸豆': '菜豆',
    '豆角': '豇豆', '长豆角': '豇豆',
    '青椒': '甜椒', '线椒': '辣椒', '螺丝椒': '辣椒',
    '地瓜': '甘薯', '番薯': '甘薯', '红薯': '甘薯',
    '芋头': '马铃薯', # 芋头≠马铃薯，但同属薯芋，此处仅作参考标记
    '去皮芋头': '净菜', '去皮山药': '净菜', '净菜（去皮蔬菜）': '净菜',
    '金针菇': '鲜食用菌', '香菇': '鲜食用菌', '平菇': '鲜食用菌',
    '木耳': '鲜食用菌', '银耳': '鲜食用菌', '杏鲍菇': '鲜食用菌',
    '西葫芦': '瓜类蔬菜', '冬瓜': '瓜类蔬菜', '南瓜': '瓜类蔬菜',
    # 水果：细则写「柑、橘」
    '丑桔': '柑、橘', '贡桔': '柑、橘', '砂糖橘': '柑、橘',
    '沃柑': '柑、橘', '蜜桔': '柑、橘', '冰糖橙': '柑、橘',
    '脐橙': '柑、橘', '血橙': '柑、橘', '芦柑': '柑、橘',
    '沃柑（注册商标）': '柑、橘',
    '苹果（烟台）': '苹果', '红富士': '苹果', '国光苹果': '苹果',
    '雪梨': '梨', '鸭梨': '梨', '皇冠梨': '梨',
    '水蜜桃': '桃', '蟠桃': '桃', '黄桃': '桃',
    '百香果': '西番莲（百香果）',
    '小台芒': '芒果', '水仙芒': '芒果', '贵妃芒': '芒果',
    '香蕉（芭蕉）': '香蕉', '芭蕉': '香蕉',
    '西瓜（黑美人）': '西瓜', '麒麟西瓜': '西瓜',
    '哈密瓜': '甜瓜类', '香瓜': '甜瓜类', '白兰瓜': '甜瓜类',
    '猕猴桃（奇异果）': '猕猴桃',
    '草莓（红颜）': '草莓',
    '龙眼（桂圆）': '龙眼',
    # 粮食加工品
    '小麦粉': '小麦粉', '特精粉': '小麦粉', '富强粉': '小麦粉',
    '馒头花卷（自制）': '馒头花卷（自制）',
    '油条（自制）': '油饼油条（自制）',
    '油饼油条(自制)': '油饼油条（自制）',
    # 餐饮食品
    '油条': '油饼油条（自制）', '油饼': '油饼油条（自制）',
    '煎饼': '除上述类别的餐饮加工自制食品',
    '武大煎饼': '除上述类别的餐饮加工自制食品',
    '鸡蛋糕': '除上述类别的餐饮加工自制食品',
    '红糖枣馒头': '馒头花卷（自制）',
    '馒头': '馒头花卷（自制）',
    '生食动物性水产品(自制)': '生食动物性水产品（自制）',
    '糕点(自制)': '糕点（自制）', '糕点（自制)': '糕点（自制）',
    '复用餐饮具（餐馆自行消毒）': '复用餐饮具（餐馆自行消毒）',
    '复用餐饮具（集中清洗消毒服务单位消毒）': '复用餐饮具（集中清洗消毒服务单位消毒）',
    # 饮料
    '包装饮用水': '包装饮用水', '饮用纯净水': '饮用纯净水',
    '雨露饮用纯净水': '饮用纯净水',
    '娃哈哈': '包装饮用水', '农夫山泉': '包装饮用水',
    '百岁山': '饮用天然矿泉水',
    '碳酸饮料(汽水)': '碳酸饮料',
    # 茶叶
    '云雾绿茶': '绿茶', '铁观音': '乌龙茶', '普洱茶': '普洱茶',
    '红茶': '红茶', '茉莉花茶': '茉莉花茶', '龙井': '绿茶',
    # 调味品
    '干姜': '干姜', '姜粉': '姜粉',
    '一明香油': '芝麻油', '小磨香油': '芝麻油',
    '辣椒油': '辣椒油',
    # 豆制品
    '贾寨豆干五香味': '其他豆制品', '薄豆皮': '其他豆制品',
    # 食糖
    '绵白糖': '白砂糖', '白砂糖': '白砂糖', '赤砂糖': '红糖',
    # 速冻
    '葡式蛋挞皮': '其他速冻食品',
    # 水产制品
    '碳烤鱿鱼丝': '即食动物性水产干制品',
    '麻辣海带': '其他水产制品',
}


def norm(s):
    if not s:
        return ''
    s = re.sub(r'[（(].*?[)）]', '', s)
    s = re.sub(r'[\s、,，。/·]', '', s)
    return s


def main():
    m = json.load(open(BASE + r'\master.json', encoding='utf-8'))
    xz = json.load(open(BASE + r'\xize_variants.json', encoding='utf-8'))
    b39 = json.load(open(BASE + r'\big39.json', encoding='utf-8'))
    recs = m['records']

    big_names = set(v['name'] for v in b39['categories'])

    # 细则品种索引（大类名 -> 归一化品种集）
    big2vars = {}
    for k, v in xz.items():
        vs = set(norm(x) for x in v['variants'] if x)
        for sub, items in v['sub'].items():
            for it in items:
                vs.add(norm(it))
        big2vars[v['name']] = vs

    total = len(recs)
    print('=' * 74)
    print('分层命中率评估 v2   总记录 = %d   细则品种 = %d' %
          (total, sum(len(v) for v in big2vars.values())))
    print('=' * 74)

    # ---------- L1 ----------
    out = [r for r in recs if r.get('big_category') not in big_names]
    print()
    print('【L1 大类合规】big_category ∈ 39 大类骨架')
    print('   %d / %d = %.2f%%' % (total - len(out), total,
                                  (total - len(out)) / total * 100))

    # ---------- L2 / L3 ----------
    l2 = l3 = 0
    l2_by = defaultdict(list)   # 未命中按大类
    l2_by_syn = Counter()      # 经同义词命中
    for r in recs:
        raw = str(r.get('food_name_canonical') or r.get('food_name_raw') or '')
        fn = norm(raw)
        bc = r.get('big_category')
        vs = big2vars.get(bc, set())
        if fn and fn in vs:
            l3 += 1
            l2 += 1
            continue
        # 经同义词映射
        tgt = SYN.get(raw)
        if tgt and norm(tgt) in vs:
            l2 += 1
            l2_by_syn[raw] += 1
            continue
        # 包含匹配
        hit = False
        for v in vs:
            if len(v) >= 2 and (v in fn or fn in v):
                hit = True
                break
        if hit:
            l2 += 1
        else:
            l2_by[bc].append(r)

    print()
    print('【L2 品类合理】映射/包含后能落到细则品种')
    print('   %d / %d = %.2f%%   （其中 %d 条靠同义词表命中）' %
          (l2, total, l2 / total * 100, sum(l2_by_syn.values())))
    print()
    print('【L3 细则原生】品种名精确等于细则品种')
    print('   %d / %d = %.2f%%' % (l3, total, l3 / total * 100))

    # ---------- 异常 ----------
    print()
    print('=' * 74)
    print('【异常A】同一品种归到多个大类')
    bg = defaultdict(Counter)
    for r in recs:
        bg[r.get('food_name_canonical') or ''][r.get('big_category')] += 1
    conf = [(k, v) for k, v in bg.items() if len(v) > 1]
    cc = sum(sum(v.values()) for _, v in conf)
    print('   %d 个品种 / %d 条 = %.2f%%' % (len(conf), cc, cc / total * 100))
    for k, v in conf:
        print('     %-22s %s' % (k, dict(v)))

    print()
    print('=' * 74)
    print('【异常B】疑似非食品（餐饮具/餐具）')
    NONFOOD = re.compile(r'餐饮具|餐碗|餐盘|餐碟|餐杯|餐勺|餐叉|筷子|自消毒|'
                        r'复用.*(碗|盘|碟|杯|勺)|碗$|盘$|碟$|勺$|杯$|筷$')
    nf = [r for r in recs if NONFOOD.search(str(r.get('food_name_canonical') or ''))]
    print('   %d / %d = %.2f%%' % (len(nf), total, len(nf) / total * 100))
    c = Counter(r.get('food_name_canonical') for r in nf)
    print('   Top: %s' % '、'.join('%s×%d' % (k, v) for k, v in c.most_common(8)))

    used = set(r.get('big_category') for r in recs)
    print()
    print('=' * 74)
    print('【异常C】骨架有、库中无数据（%d 个，须保留）' % len(big_names - used))
    print('   %s' % '、'.join(sorted(big_names - used)))

    bad = [r for r in recs if r.get('sub_category')
           and not str(r['sub_category']).startswith(str(r.get('big_category')))]
    print()
    print('【异常D】sub_category 前缀与 big_category 不一致 = %d 条' % len(bad))

    # ---------- L2 未命中 ----------
    print()
    print('=' * 74)
    print('【L2 未命中明细】共 %d 条，需判定"细则外商品名"还是"归错"'
          % sum(len(v) for v in l2_by.values()))
    for k in sorted(l2_by, key=lambda x: -len(l2_by[x])):
        v = l2_by[k]
        print()
        print('  ■ %s  (%d 条 / %d 品种)' % (k, len(v), len(set(
            str(r.get('food_name_canonical')) for r in v))))
        cc2 = Counter(str(r.get('food_name_canonical'))[:20] for r in v)
        for name, n in cc2.most_common(14):
            print('      %-24s %d' % (name, n))
        if len(cc2) > 14:
            print('      ... 另 %d 个' % (len(cc2) - 14))


if __name__ == '__main__':
    main()