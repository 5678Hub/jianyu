"""v82-fix82 整体核对: 19 个 idx 空 L3/L4 节点详细报告

对每个 idx 空节点，列出:
1. 祖先 L1/L2/L3 通类 row (walkExact fallback 候选)
2. 同 L1 章节中 food 字段含节点关键词的 row (复制挂载候选)
3. 节点自身是否在 PDF row 中有 L3/L4 字段 (idx 命中失败原因)
4. 建议处理方案
"""
import json, re, sys

# ---------- 加载数据 ----------
with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

tree = d['appendix_a1']['tree']

# 收集所有 items（合并 12 项污染物）
all_items = []  # (table_no, pollutant, item)
for con in d['contaminants']:
    for it in con['items']:
        all_items.append((con['table_no'], con['contaminant'], it))

# 按 a1l 路径索引
def path_key(a1l1, a1l2, a1l3, a1l4):
    parts = [p for p in [a1l1, a1l2, a1l3, a1l4] if p]
    return '|'.join(parts)

# 按 a1l1+a1l2+a1l3+a1l4 索引
by_path = {}
for tno, pol, it in all_items:
    p = path_key(it.get('a1_l1',''), it.get('a1_l2',''), it.get('a1_l3',''), it.get('a1_l4',''))
    by_path.setdefault(p, []).append((tno, pol, it))

# 按 a1l1 索引
by_l1 = {}
for tno, pol, it in all_items:
    l1 = it.get('a1_l1','')
    if l1:
        by_l1.setdefault(l1, []).append((tno, pol, it))

# 归一化（用于 keyword 匹配）
def norm(s):
    if not s:
        return ''
    s = s.replace('（','(').replace('）',')')
    s = re.sub(r'[\s,，、。\.]','', s)
    s = re.sub(r'\([^)]*\)', '', s)  # 删括号内容
    return s

# 19 个 idx 空节点
EMPTY_NODES = [
    # 肉及肉制品
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '其他熟肉制品'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '发酵肉制品类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '油炸肉类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '熟肉干制品（例如:肉干、肉松等）'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '肉灌肠类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '肉类罐头'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '西式火腿（熏烤、烟熏、蒸煮火腿）类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '酱卤肉制品类'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '预制肉制品', '腌腊肉制品类（例如：咸肉、腊肉、板鸭、中式火腿、腊肠等）'),
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '预制肉制品', '调理肉制品（生肉添加调理料）'),
    # 谷物及其制品
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '其他小麦粉制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '发酵面制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '生干面制品'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '生湿面制品（例如：面条、饺子皮、馄饨皮、烧麦皮等）'),
    ('谷物及其制品(不包括焙烤制品)', '谷物制品', '小麦粉制品', '面糊（例如：用于鱼和禽肉的拖面糊）、裹粉、煎炸粉'),
    # 水产动物及其制品
    ('水产动物及其制品', '鲜、冻水产动物', '软体动物', '其他软体动物'),
    ('水产动物及其制品', '鲜、冻水产动物', '软体动物', '头足类'),
    ('水产动物及其制品', '鲜、冻水产动物', '软体动物', '腹足类'),
    ('水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'),
]

print('='*80)
print('v82-fix82 任务3 整体核对：19 个 idx 空 L3/L4 节点详细分析')
print('='*80)

current_l1 = None
for l1, l2, l3, l4 in EMPTY_NODES:
    if l1 != current_l1:
        print()
        print(f'\n【{l1}】')
        print('='*80)
        current_l1 = l1

    full_path = f'{l1}|{l2}|{l3}|{l4}'
    path_short = f'{l1} → {l2} → {l3} → {l4}'

    print(f'\n--- {path_short} ---')

    # 1. 节点自身 idx 是否有 row?
    self_rows = by_path.get(full_path, [])
    print(f'  [1] 节点自身 idx row: {len(self_rows)} 条')

    if self_rows:
        for tno, pol, it in self_rows[:5]:
            print(f'      [{tno}] {pol} food={it["food"][:40]} val={it["limit_value"][:8]}/{it.get("sub_value","")[:8]}')

    # 2. 祖先 fallback row (L3/L2/L1)
    p_l3 = f'{l1}|{l2}|{l3}'
    p_l2 = f'{l1}|{l2}'
    p_l1 = l1
    p_l3_any = f'{l1}|{l2}|{l3}|'  # L3 任意 L4 (例如畜禽内脏)

    ancestors = {
        'L3 通类 (L1+L2+L3, 任意 L4)': by_path.get(p_l3_any, []),
        'L2 通类 (L1+L2, 任意 L3/L4)': by_path.get(f'{p_l2}|', []),
        'L2 通类 (L1+L2, 无 L3)': [r for r in by_l1.get(l1, []) if r[2].get('a1_l2') == l2 and not r[2].get('a1_l3') and not r[2].get('a1_l4')],
        'L1 通类 (L1, 无 L2)': [r for r in by_l1.get(l1, []) if not r[2].get('a1_l2')],
    }

    print(f'  [2] 祖先 fallback row 候选:')
    for label, rows in ancestors.items():
        if rows:
            # 按污染物分组
            polys = {}
            for tno, pol, it in rows:
                polys.setdefault(pol, []).append(f'val={it["limit_value"][:8]}/{it.get("sub_value","")[:8]} food={it["food"][:30]}')
            print(f'    {label}:')
            for pol, vals in polys.items():
                print(f'      {pol}: {len(vals)} 条 - {", ".join(vals[:3])}')

    # 3. 同 L1 章节 food 字段含节点关键词的 row
    node_kw = norm(l4)
    matched_food = []
    for tno, pol, it in by_l1.get(l1, []):
        food_n = norm(it.get('food',''))
        if node_kw in food_n:
            matched_food.append((tno, pol, it))
    print(f'  [3] 同 L1 章节 food 字段含「{node_kw}」关键词 row: {len(matched_food)} 条')
    for tno, pol, it in matched_food[:8]:
        print(f'    [{tno}] {pol} food={it["food"][:40]} val={it["limit_value"][:8]}/{it.get("sub_value","")[:8]} | L1={it.get("a1_l1","")} L2={it.get("a1_l2","")[:20]} L3={it.get("a1_l3","")[:20]} L4={it.get("a1_l4","")[:20]}')

    # 4. 节点 L4 名本身是否在 PDF row 中出现 (排除自身)
    l4_kws = [l4, norm(l4)]
    for kw in l4_kws:
        if not kw:
            continue
        in_rows = []
        for tno, pol, it in by_l1.get(l1, []):
            food_n = norm(it.get('food',''))
            if kw in food_n:
                # 已经 print 过则跳过
                if (tno, pol, it) in matched_food:
                    continue
                in_rows.append((tno, pol, it))
        if in_rows:
            print(f'  [4] L4 关键词「{kw}」命中非 [3] 的额外 row: {len(in_rows)} 条')
            for tno, pol, it in in_rows[:3]:
                print(f'    [{tno}] {pol} food={it["food"][:50]} val={it["limit_value"][:8]}/{it.get("sub_value","")[:8]} | L3={it.get("a1_l3","")[:20]} L4={it.get("a1_l4","")[:20]}')
