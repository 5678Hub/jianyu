"""
v82-fix27 完整回归测试：
  - v82-fix24: 蒸馏酒/发酵酒 idx=1 (L2)
  - v82-fix25: 0.04 葡萄汁 不 leak 到 L3 果蔬汁（浆）类饮料 idx
  - v82-fix26: 空叶子节点(畜禽肉/蔬菜泥/坚果及籽类制品)可点击 + 适用污染物=—
  - v82-fix27: 花生 (镉 ≤0.5) 注册到 L3 生干坚果及籽类
"""
import re, json

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))
tree = data['appendix_a1']['tree']

# 移植 norm + matchItemToPaths (与 v82-fix27 同步)
def norm(s):
    s = s or ''
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

def is_footnote(s):
    v = (s or '').strip()
    return bool(re.fullmatch(r'[a-zA-Z]{1,3}', v) or re.fullmatch(r'\d{1,2}', v))

def walk_food(nodes, food_norm, food_core_norm, cur_path):
    best = None
    for n in nodes:
        nn = norm(n['name'])
        if nn == food_norm or nn == food_core_norm:
            deepest = None
            def go_deeper(nn2, p):
                nonlocal deepest
                if not nn2.get('children'):
                    deepest = p; return
                for c in nn2['children']:
                    cn = norm(c['name'])
                    if cn == food_core_norm or cn.startswith(food_core_norm) or (len(food_core_norm) >= 3 and food_core_norm in cn):
                        go_deeper(c, p + [c['name']])
            go_deeper(n, cur_path + [n['name']])
            if deepest and (not best or len(deepest) > len(best)):
                best = deepest
            elif not best:
                best = cur_path + [n['name']]
        if n.get('children'):
            sub = walk_food(n['children'], food_norm, food_core_norm, cur_path + [n['name']])
            if sub and (not best or len(sub) > len(best)):
                best = sub
    return best

def match_item_to_paths(item, tree):
    a1_path_raw = []
    last = None
    for v in [item.get('a1_l1',''), item.get('a1_l2',''), item.get('a1_l3',''), item.get('a1_l4','')]:
        if v and v != last:
            a1_path_raw.append(v); last = v
    a1_path = list(a1_path_raw)
    if a1_path and is_footnote(a1_path[-1]) and item.get('food'):
        found = False
        def probe(nodes):
            nonlocal found
            for n in nodes:
                if norm(n['name']) == norm(item['food']):
                    found = True; return
                if n.get('children'): probe(n['children'])
        probe(tree)
        if found: a1_path[-1] = item['food']
        else: a1_path.pop()
    matched = []
    if a1_path:
        def walk(nodes, path, idx):
            if idx >= len(a1_path): return
            target = norm(a1_path[idx])
            target_raw = a1_path[idx]
            target_has_brackets = bool(re.search(r'[()（）\[\]【】]', target_raw))
            matched_here = False
            for n in nodes:
                nn = norm(n['name'])
                m1 = nn == target
                if not m1 and idx == len(a1_path) - 1 and not target_has_brackets and len(target) >= 3 and nn.startswith(target):
                    m1 = True
                if not m1 and idx >= 1:
                    sib_core = re.sub(r'[([{【（].*$', '', n['name']).strip()
                    sib_core_norm = norm(sib_core)
                    if sib_core_norm == target and len(sib_core) > 0 and len(nn) > len(target):
                        m1 = True
                if m1:
                    matched_here = True
                    cp = path + [n['name']]
                    if idx < len(a1_path) - 1 and n.get('children'):
                        walk(n['children'], cp, idx + 1)
                    else:
                        matched.append(cp)
            if not matched_here and idx == len(a1_path) - 1 and len(path) > 0:
                matched.append(list(path))
        walk(tree, [], 0)
    if not matched and item.get('food'):
        fn = norm(item['food'])
        fc = re.sub(r'[([{【（].*$', '', item['food']).strip()
        fcn = norm(fc)
        best = walk_food(tree, fn, fcn, [])
        if best: matched.append(best)
    return matched

# 构建 idx
idx = {}
for contam in data['contaminants']:
    for it in contam.get('items', []):
        if it.get('has_limit') is False: continue
        paths = match_item_to_paths(it, tree)
        for p in paths:
            pk = '|'.join(p)
            idx.setdefault(pk, []).append((contam['contaminant'], it.get('limit_value'), it.get('food','')[:30]))

def stats_for_path(path):
    pk = '|'.join(path)
    items = idx.get(pk, [])
    return len(items)

# 跑回归
print('=' * 80)
print('v82-fix27 回归测试')
print('=' * 80)
print()

print('--- 坚果及籽类 (本 fix27 修复) ---')
for node_path in [
    ['坚果及籽类'],
    ['坚果及籽类', '生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）'],
    ['坚果及籽类', '坚果及籽类制品'],
    ['坚果及籽类', '坚果及籽类制品', '熟制坚果及籽类（带壳、脱壳、包衣）'],
    ['坚果及籽类', '坚果及籽类制品', '坚果及籽类罐头'],
]:
    pk = '|'.join(node_path)
    items = idx.get(pk, [])
    print(f"  {' > '.join(node_path)}")
    print(f"    限量数 = {len(items)}")
    for c, lv, food in items:
        print(f"      {c} ≤{lv} - {food}")

print()
print('--- v82-fix24 蒸馏酒/发酵酒 ---')
for node_path in [
    ['酒类', '蒸馏酒（例如：白酒、白兰地、威士忌、伏特加、朗姆酒等）'],
    ['酒类', '发酵酒（例如：葡萄酒、黄酒、果酒、啤酒等）'],
]:
    pk = '|'.join(node_path)
    items = idx.get(pk, [])
    print(f"  {' > '.join(node_path)}: {len(items)} 条")
    for c, lv, food in items[:3]:
        print(f"    {c} ≤{lv} - {food}")

print()
print('--- v82-fix25 葡萄汁 ---')
for node_path in [
    ['饮料类', '果蔬汁类及其饮料', '果蔬汁（浆）'],
    ['饮料类', '果蔬汁类及其饮料', '果蔬汁（浆）类饮料'],
]:
    pk = '|'.join(node_path)
    items = idx.get(pk, [])
    found_juice = any('葡萄汁' in food for _, _, food in items)
    print(f"  {' > '.join(node_path)}: {len(items)} 条, 包含葡萄汁? {found_juice}")

print()
print('--- v82-fix26 空叶子节点 ---')
for node_path in [
    ['肉及肉制品', '肉类(生鲜肉、冷却肉、冷冻肉等)', '畜禽肉'],
    ['肉及肉制品', '肉类(生鲜肉、冷却肉、冷冻肉等)', '畜禽内脏'],
    ['蔬菜及其制品（包括薯类，不包括食用菌）', '蔬菜制品', '蔬菜泥（酱）'],
    ['肉及肉制品', '肉制品(包括内脏制品、血制品)', '油炸肉类'],
    ['肉及肉制品', '肉制品(包括内脏制品、血制品)', '西式火腿'],
    ['肉及肉制品', '肉制品(包括内脏制品、血制品)', '肉制品罐头'],
    ['坚果及籽类', '坚果及籽类制品', '熟制坚果及籽类（带壳、脱壳、包衣）'],
    ['坚果及籽类', '坚果及籽类制品', '坚果及籽类罐头'],
    ['坚果及籽类', '坚果及籽类制品', '坚果及籽类的泥（酱）（例如：花生酱等）'],
]:
    pk = '|'.join(node_path)
    items = idx.get(pk, [])
    name = node_path[-1]
    print(f"  {name[:30]}: {len(items)} 条")