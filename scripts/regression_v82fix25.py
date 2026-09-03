"""
v82-fix25 综合回归测试。
模拟完整 walkExact + Fallback B + v23/v29 + v30 + v82-fix22 multi-sub
+ v82-fix24 statsForPath(取消 a1_lN 深度过滤) + v82-fix25 (prefix gate)
逻辑,确认关键 path 的注册 row 数与用户期望一致。
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

def has_brackets(s):
    return bool(re.search(r'[()（）\[\]【】]', s or ''))

def get_excludes(food):
    """提取「(...除外)」括号内,排除掉所有 '除外' 的内容"""
    if not food: return []
    result = []
    depth = 0
    current = ''
    in_paren = False
    for ch in food:
        if ch in '([{' or ch in '（【':
            if depth == 0 and not in_paren:
                in_paren = True
                continue
            elif in_paren:
                current += ch
                depth += 1
        elif ch in ')]}' or ch in '）】':
            if in_paren:
                if depth > 0:
                    current += ch
                    depth -= 1
                else:
                    # 结束
                    result.append(current)
                    current = ''
                    in_paren = False
        elif in_paren:
            current += ch
    return [r for r in result if '除外' in r]

def food_contains_sib_core(food, sib_core):
    food_lc = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', food or '').lower()
    sib_core_lc = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', sib_core or '').lower()
    return bool(sib_core_lc) and sib_core_lc in food_lc

def walk_exact(a1path, tree):
    """v82-fix25: prefix-match gated by targetHasBrackets"""
    if not a1path: return []
    matched_paths = []
    def _walk(nodes, path, idx):
        if idx >= len(a1path): return
        target = norm(a1path[idx])
        target_raw = a1path[idx] or ''
        target_has_brackets = has_brackets(target_raw)
        matched_here = False
        for n in nodes:
            nname = norm(n['name'])
            matched = (nname == target)
            # 末层 fallback A: prefix match gated
            if (not matched and idx == len(a1path) - 1
                    and not target_has_brackets
                    and len(target) >= 3
                    and nname.startswith(target)):
                matched = True
            # core 匹配 (idx >= 1)
            if not matched and idx >= 1:
                sib_core = re.sub(r'[([{【（].*$', '', n['name']).strip()
                sib_core_norm = norm(sib_core)
                if (sib_core_norm == target
                        and len(sib_core) > 0
                        and len(nname) > len(target)):
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

def is_l2_multi_sub(it, path):
    """v82-fix22: v30 扩散只对多子类列举 row 触发"""
    norm_food_prefix = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', it.get('food', '') or '').lower()
    mount_name2 = path[1] if len(path) > 1 else None
    mount_core2 = re.sub(r'[([{【（].*$', '', mount_name2 or '').strip()
    mount_core2 = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', mount_core2).lower()
    return (len(path) == 2
            and not (it.get('a1_l3') or '').strip()
            and it.get('food')
            and mount_core2
            and not norm_food_prefix.startswith(mount_core2))

def get_registered_paths(it, tree):
    """完整模拟 v23/v29 + v30 + v82-fix22 + Fallback B"""
    ap = [it.get('a1_l1'), it.get('a1_l2'), it.get('a1_l3'), it.get('a1_l4')]
    ap = [x for x in ap if x]
    dedup = []
    for i, v in enumerate(ap):
        if i == 0 or v != ap[i-1]:
            dedup.append(v)
    paths = walk_exact(dedup, tree)
    food = it.get('food', '')
    # v23/v29 + v30 sibling expansion
    for p in list(paths):
        is_l2 = is_l2_multi_sub(it, p)
        if not (len(p) >= 3 or is_l2) or not food: continue
        start_path = p[:-1] if not is_l2 else p
        cur = None
        for sp in start_path:
            children = cur['children'] if cur else tree
            f = next((c for c in children if c['name'] == sp), None)
            if not f: break
            cur = f
        if not cur or not cur.get('children'): continue
        current_leaf = None if is_l2 else p[-1]
        excludes = get_excludes(food)
        for sib in cur['children']:
            if not is_l2 and sib['name'] == current_leaf: continue
            if not sib['name'] or len(sib['name']) < 2: continue
            sib_core = re.sub(r'[([{【（].*$', '', sib['name']).strip()
            if not sib_core or len(sib_core) < 2: continue
            # 简化 v35: 跳过「除外」检查(过于复杂,本次回归测试不模拟)
            if food_contains_sib_core(food, sib_core) or (len(sib_core) >= 3 and sib['name'] in food):
                new_p = start_path + [sib['name']]
                if new_p not in paths:
                    paths.append(new_p)
    return paths

# 收齐所有 rows
all_rows = []
for c in DATA['contaminants']:
    for it in c.get('items', []):
        it['_table_no'] = c['table_no']
        all_rows.append(it)

print(f'Total rows: {len(all_rows)}')
print()

# 用户期望的 statsForPath(取消深度过滤)结果
EXPECTED = [
    # 用户报告 issue + fix 验证
    ('L2 蒸馏酒', ['酒类', '蒸馏酒（例如：白酒、白兰地、威士忌、伏特加、朗姆酒等）'], 1,
     'v82-fix24: 黄酒 0.5 不应该漏'),
    ('L2 发酵酒', ['酒类', '发酵酒（例如：葡萄酒、黄酒、果酒、啤酒等）'], 1,
     'v82-fix24: 白酒 0.5 不应该漏'),
    ('L2 配制酒', ['酒类', '配制酒'], 0,
     'no rows'),
    # v82-fix25 关键: 不再 leak 到 L3 果蔬汁（浆）类饮料
    ('L3 果蔬汁（浆）类饮料', ['饮料类', '果蔬汁类及其饮料（例如：苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等）', '果蔬汁（浆）类饮料'], 0,
     'v82-fix25: 0.04 葡萄汁 不应再 leak'),
    # v82-fix23 验证: L3 果蔬汁（浆） 应有 1 条
    ('L3 果蔬汁（浆）', ['饮料类', '果蔬汁类及其饮料（例如：苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等）', '果蔬汁（浆）'], 1,
     '0.04 葡萄汁 应在'),
    # v82-fix22: L3 块根和块茎蔬菜 应显示 3 (姜 0.2 + 薯类 0.2 + 0.1 Cd)
    ('L3 块根和块茎蔬菜', ['蔬菜及其制品（包括薯类，不包括食用菌）', '新鲜蔬菜（未经加工的、经表面处理的、去皮或预切的、冷冻的蔬菜）', '块根和块茎蔬菜（例如：薯类、胡萝卜、萝卜、生姜等）'], None,
     '依赖 v82-fix19 之前的逻辑,先不验证具体数'),
]

# 找目标路径
def find_path(nodes, target_path):
    if not target_path: return None
    head, *rest = target_path
    for n in nodes:
        if n['name'] == head:
            if not rest: return n
            if n.get('children'):
                r = find_path(n['children'], rest)
                if r: return r
    return None

print('=== 关键 path 的 statsForPath(取消深度过滤)验证 ===')
for label, tg, expected, note in EXPECTED:
    node = find_path(tree, tg)
    if not node:
        print(f'  ❌ {label}: 找不到 node')
        continue
    rows_in = []
    for r in all_rows:
        if not r.get('has_limit', True): continue
        if tg in get_registered_paths(r, tree):
            rows_in.append(r)
    exp_str = f'(期望 {expected})' if expected is not None else ''
    status = '✓' if expected is None or len(rows_in) == expected else '❌'
    print(f'  {status} {label}: 注册 row 数 = {len(rows_in)} {exp_str}  | {note}')
    for r in rows_in[:5]:
        print(f'      - food={r.get("food")!r} limit={r.get("limit_value")} '
              f'a1_l3={r.get("a1_l3")!r}')
    if len(rows_in) > 5:
        print(f'      ... ({len(rows_in)-5} more)')
print()

# v82-fix22 v30 多子类列举验证: row '稻谷、糙米、...、小麦粉' 应推到 L3 children
print('=== v82-fix22 v30 多子类列举 验证 ===')
# 找一个多子类列举 row
multi_sub_rows = []
for r in all_rows:
    food = r.get('food', '') or ''
    if (re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', food).lower().startswith('稻谷糙米')
            or re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', food).lower().startswith('稻谷')):
        multi_sub_rows.append(r)
print(f'找到 {len(multi_sub_rows)} 个多子类 row (例: 稻谷开头)')
if multi_sub_rows:
    r = multi_sub_rows[0]
    paths = get_registered_paths(r, tree)
    print(f'  示例 row food={r.get("food")[:50]!r}... 注册 paths:')
    for p in paths:
        print(f'    - {p}')
print()

# v82-fix22 L2 通类项验证: 「果蔬汁类及其饮料(…除外)」 应 NOT 扩散到 L3
print('=== v82-fix22 L2 通类项(食品类别本身)不扩散验证 ===')
tonglei_rows = []
for r in all_rows:
    food = r.get('food', '') or ''
    if '果蔬汁类及其饮料' in food and '除外' in food:
        tonglei_rows.append(r)
print(f'找到 {len(tonglei_rows)} 个 L2 通类项 row')
for r in tonglei_rows[:2]:
    paths = get_registered_paths(r, tree)
    # 检查是否 leak 到 L3
    leaked_to_l3 = [p for p in paths if len(p) >= 3]
    print(f'  food={r.get("food")[:30]!r}... | 注册 path 数 = {len(paths)} | L3 leak = {len(leaked_to_l3)}')
    for p in paths:
        print(f'    - {p}')
