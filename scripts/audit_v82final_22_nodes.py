"""v82-final 22 节点 PDF 深度校对 - 核对每个节点在 PDF 表 1-9 中的 row 表达"""
import json, re

with open('data/gb2762/gb2762_2025.json','r',encoding='utf-8') as f:
    d = json.load(f)

def norm(s):
    if not s: return ''
    s = str(s)
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】+]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s

# 收集所有污染物表
all_items = []
for con in d['contaminants']:
    for it in con['items']:
        all_items.append({
            'table_no': con['table_no'],
            'contaminant': con['contaminant'],
            'symbol': con.get('symbol',''),
            'food': it.get('food',''),
            'limit_value': it.get('limit_value',''),
            'sub_value': it.get('sub_value',''),
            'modif': it.get('modif',''),
            'a1_l1': it.get('a1_l1',''),
            'a1_l2': it.get('a1_l2',''),
            'a1_l3': it.get('a1_l3',''),
            'a1_l4': it.get('a1_l4',''),
        })

# 22 个 ancestorsLevels 段只显示 1 条 Pb row 的节点
nodes = [
    ('水果及其制品', '水果制品', '水果罐头', None),
    ('水果及其制品', '水果制品', '醋、油或盐渍水果', None),
    ('水果及其制品', '水果制品', '发酵的水果制品', None),
    ('水果及其制品', '水果制品', '煮熟的或油炸的水果', None),
    ('水果及其制品', '水果制品', '水果甜品', None),
    ('水果及其制品', '水果制品', '其他水果制品', None),
    ('蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '蔬菜罐头', None),
    ('蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '蔬菜泥（酱）', None),
    ('蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '经水煮或油炸的蔬菜', None),
    ('蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '其他蔬菜制品', None),
    ('豆类及其制品', '豆类制品', '发酵豆制品（例如：腐乳类、纳豆、豆豉、豆豉制品等）', None),
    ('豆类及其制品', '豆类制品', '豆类罐头', None),
    ('豆类及其制品', '豆类制品', '其他豆类制品（包括豆沙馅）', None),
    ('藻类及其制品', '新鲜藻类（未经加工的、经表面处理的）', '其他新鲜藻类', None),
    ('藻类及其制品', '藻类制品', '藻类罐头', None),
    ('藻类及其制品', '藻类制品', '干制藻类', None),
    ('藻类及其制品', '藻类制品', '盐渍藻类', None),
    ('藻类及其制品', '藻类制品', '经水煮或油炸的藻类', None),
    ('坚果及籽类', '坚果及籽类制品', '熟制坚果及籽类（带壳、脱壳、包衣）', None),
    ('坚果及籽类', '坚果及籽类制品', '坚果及籽类罐头', None),
    ('坚果及籽类', '坚果及籽类制品', '坚果及籽类的泥（酱）（例如：花生酱等）', None),
    ('坚果及籽类', '坚果及籽类制品', '其他坚果及籽类制品（例如：腌渍的果仁等）', None),
]

# 模拟 isApplicableToPath
def is_applicable(it, l1, l2, l3, l4):
    food = it.get('food','')
    a1l1 = norm(it.get('a1_l1',''))
    a1l2 = norm(it.get('a1_l2',''))
    a1l3 = norm(it.get('a1_l3',''))
    a1l4 = it.get('a1_l4','')
    l1n = norm(l1)
    l2n = norm(l2)
    l3n = norm(l3)

    # a1l1 匹配 (同 L1)
    if a1l1 != l1n:
        return False
    # a1l3/l4 空 (L2 通类 row, 这是 ancestorsLevels 显示的 row)
    if a1l3 or a1l4:
        return False
    # a1l2 = l2
    if a1l2 != l2n:
        return False

    # 除外列表检查
    idx = food.rfind('除外')
    if idx >= 0:
        openIdx = -1
        depth = 0
        for i in range(idx - 1, -1, -1):
            if food[i] in ')）':
                depth += 1
            elif food[i] in '(（':
                if depth == 0:
                    openIdx = i
                    break
                depth -= 1
        if openIdx >= 0:
            exclude_str = food[openIdx+1:idx]
            excl_list = re.split(r'[、,,，]', exclude_str)
            for exc in excl_list:
                norm_exc = norm(exc)
                if len(norm_exc) < 2:
                    continue
                for name in [l1, l2, l3, l4] if l4 else [l1, l2, l3]:
                    norm_name = norm(name)
                    if norm_name == norm_exc:
                        return False
                    name_core = re.sub(r'[\(\[【（].*\$', '', name).strip()
                    name_core = norm(name_core)
                    if name_core == norm_exc:
                        return False
    return True

# 对每个节点,列出 a1l1=l1, a1l2=l2, a1l3/l4=空 的 row (即 ancestorsLevels 段可能 row)
print('=== 22 节点 PDF 二次核对 ===\n')
print('逻辑: 找 a1l1=l1, a1l2=l2, a1l3/l4=空 的所有 row (经 isApplicableToPath 过滤)')
print()

for l1, l2, l3, l4 in nodes:
    print(f'\n## {l3}')
    print(f'   L1={l1[:30]} | L2={l2[:20]}')
    # 找 ancestorsLevels 段 row (L2 通类 row + L1 通类 row)
    ancestors_rows = []
    for it in all_items:
        a1l1 = norm(it.get('a1_l1',''))
        a1l2 = it.get('a1_l2','')
        a1l3 = it.get('a1_l3','')
        a1l4 = it.get('a1_l4','')
        if a1l1 != norm(l1): continue
        if a1l3 or a1l4: continue  # 必须是 L2/L1 通类 row
        if a1l2 == l2:  # L2 通类 row
            if is_applicable(it, l1, l2, l3, l4):
                ancestors_rows.append(it)
        elif not a1l2:  # L1 通类 row
            if is_applicable(it, l1, l2, l3, l4):
                ancestors_rows.append(it)

    # 找 idx 空检查
    pk = '|'.join(norm(p) for p in [l1, l2, l3] if p)
    idx_o_rows = [it for it in all_items if '|'.join(norm(p) for p in [it.get(f'a1_l{i}','') for i in [1,2,3,4]] if p) == pk]

    print(f'   ancestorsLevels 段 row ({len(ancestors_rows)} 条):')
    for it in ancestors_rows:
        sv = it.get('sub_value','')
        print(f'     [{it["table_no"]}{it["contaminant"]}] val={it["limit_value"]}{("/"+sv) if sv else ""} {it["food"][:50]}')

    # 找 a1l1=l1 但 a1l2!=l2, a1l3/l4=空 的 row (v82-fix83 撤回的跨 L2 通类 row)
    cross_l2_rows = []
    for it in all_items:
        a1l1 = norm(it.get('a1_l1',''))
        a1l2 = it.get('a1_l2','')
        a1l3 = it.get('a1_l3','')
        a1l4 = it.get('a1_l4','')
        if a1l1 != norm(l1):
            continue
        if not a1l2 or a1l2 == l2:
            continue
        if a1l3 or a1l4:
            continue
        # isApplicableToPath 检查
        if is_applicable(it, l1, l2, l3, l4):
            cross_l2_rows.append(it)

    if cross_l2_rows:
        print(f'   ⚠️  同 L1 跨 L2 通类 row (v82-fix85 已撤回, 不显示, 仅供参考) ({len(cross_l2_rows)} 条):')
        for it in cross_l2_rows:
            print(f'     [{it["table_no"]}{it["contaminant"]}] val={it["limit_value"]} L2={it["a1_l2"][:20]} {it["food"][:40]}')

    if idx_o_rows:
        print(f'   ⭐ idx 命中 row ({len(idx_o_rows)} 条) — 应不出现, 如出现说明数据问题:')
        for it in idx_o_rows:
            print(f'     [{it["table_no"]}{it["contaminant"]}] val={it["limit_value"]} {it["food"][:50]}')
