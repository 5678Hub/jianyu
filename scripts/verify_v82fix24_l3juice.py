"""
v82-fix24 专项验证 - 快速版。
"""
import json
import re

DATA = json.load(open('data/gb2762/gb2762_2025.json', encoding='utf-8'))
tree = DATA['appendix_a1']['tree']

def norm(s):
    if not s: return ''
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

# 找目标 paths
target_l3_guozhi = None
target_l2_zheng = None
target_l2_fa = None
target_l2_peizhi = None
for n in tree:
    if n['name'] == '饮料类':
        for c2 in n.get('children', []):
            if '果蔬汁类及其饮料' in c2['name']:
                for c3 in c2.get('children', []):
                    if '果蔬汁（浆）类饮料' in c3['name']:
                        target_l3_guozhi = [n['name'], c2['name'], c3['name']]
    elif n['name'] == '酒类':
        for c2 in n.get('children', []):
            if '蒸馏酒' in c2['name']:
                target_l2_zheng = [n['name'], c2['name']]
            elif '发酵酒' in c2['name']:
                target_l2_fa = [n['name'], c2['name']]
            elif '配制酒' in c2['name']:
                target_l2_peizhi = [n['name'], c2['name']]

print('Target paths:')
print(f'  L3 果蔬汁（浆）类饮料: {target_l3_guozhi[-1] if target_l3_guozhi else None}')
print(f'  L2 蒸馏酒: {target_l2_zheng[-1] if target_l2_zheng else None}')
print(f'  L2 发酵酒: {target_l2_fa[-1] if target_l2_fa else None}')
print(f'  L2 配制酒: {target_l2_peizhi[-1] if target_l2_peizhi else None}')
print()

# 列出 a1_l2 包含「果蔬汁类及其饮料」的 row (优化搜索)
target_l2_guozhi_norm = norm('果蔬汁类及其饮料')
target_l2_zheng_norm = norm('蒸馏酒')
target_l2_fa_norm = norm('发酵酒')
target_l2_peizhi_norm = norm('配制酒')

candidates = []
for c in DATA['contaminants']:
    for it in c.get('items', []):
        l1 = norm(it.get('a1_l1', ''))
        l2 = norm(it.get('a1_l2', ''))
        l3 = norm(it.get('a1_l3', ''))
        l4 = norm(it.get('a1_l4', ''))
        # 命中以上任一 target l2 就看
        if (l1 == norm('饮料类') or l1 == norm('酒类')) and (target_l2_guozhi_norm in l2
                or target_l2_zheng_norm in l2
                or target_l2_fa_norm in l2
                or target_l2_peizhi_norm in l2
                or target_l2_guozhi_norm in l3
                or target_l2_guozhi_norm in l4):
            candidates.append((c['table_no'], it))

print(f'candidates row count: {len(candidates)}')
print()

# 模拟 walkExact + Fallback B + v23 sibling
def walk_exact_simple(a1path, tree):
    if not a1path: return []
    matched_paths = []

    def _walk(nodes, path, idx):
        if idx >= len(a1path): return
        target = norm(a1path[idx])
        matched_here = False
        for n in nodes:
            nname = norm(n['name'])
            matched = (nname == target)
            if not matched and idx == len(a1path) - 1 and len(target) >= 3 and nname.startswith(target):
                matched = True
            if matched:
                matched_here = True
                cur_path = path + [n['name']]
                if idx < len(a1path) - 1 and n.get('children'):
                    _walk(n['children'], cur_path, idx + 1)
                else:
                    matched_paths.append(cur_path)
        if (not matched_here and idx == len(a1path) - 1
                and len(path) > 0):
            matched_paths.append(path[:])

    _walk(tree, [], 0)
    return matched_paths

def get_registered_paths(it, tree):
    ap = [it.get('a1_l1'), it.get('a1_l2'), it.get('a1_l3'), it.get('a1_l4')]
    ap = [x for x in ap if x]
    # 去重连续
    dedup = []
    for i, v in enumerate(ap):
        if i == 0 or v != ap[i-1]:
            dedup.append(v)
    paths = walk_exact_simple(dedup, tree)
    # v23 sibling expansion
    food = it.get('food', '')
    for p in list(paths):
        if len(p) < 3 or not food: continue
        start_path = p[:-1]
        cur = None
        for sp in start_path:
            children = cur['children'] if cur else tree
            f = next((c for c in children if c['name'] == sp), None)
            if not f: break
            cur = f
        if cur and cur.get('children'):
            for sib in cur['children']:
                if sib['name'] == p[-1]: continue
                sib_core = re.sub(r'[([{【（].*$', '', sib['name']).strip()
                sib_core_lc = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', sib_core).lower()
                food_lc = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', food).lower()
                if (sib_core and sib_core_lc in food_lc) or (len(sib_core) >= 3 and sib['name'] in food):
                    new_p = start_path + [sib['name']]
                    if new_p not in paths:
                        paths.append(new_p)
    return paths

print('=== 用户报告问题: L2 蒸馏酒/发酵酒/配制酒 statsForPath ===')
for label, tg in [('蒸馏酒', target_l2_zheng), ('发酵酒', target_l2_fa), ('配制酒', target_l2_peizhi)]:
    if not tg:
        print(f'  L2 {label}: not found')
        continue
    rows_in = []
    for _, r in candidates:
        if not r.get('has_limit', True): continue
        if tg in get_registered_paths(r, tree):
            rows_in.append(r)
    print(f'  L2 {label} 注册 row 数 (v82-fix24 statsForPath) = {len(rows_in)}')
    for r in rows_in:
        print(f'    - food={r.get("food")!r} limit={r.get("limit_value")} '
              f'a1_l3={r.get("a1_l3")!r} hl={r.get("has_limit")}')
print()

print('=== L3 果蔬汁（浆）类饮料 注册 row 检查 ===')
rows_in = []
for _, r in candidates:
    if not r.get('has_limit', True): continue
    if target_l3_guozhi in get_registered_paths(r, tree):
        rows_in.append(r)
print(f'  count = {len(rows_in)}')
for r in rows_in:
    print(f'  - food={r.get("food")!r} limit={r.get("limit_value")} '
          f'a1_l3={r.get("a1_l3")!r} hl={r.get("has_limit")}')
