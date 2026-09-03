# -*- coding: utf-8 -*-
"""验证 v82-fix36: L2 谷物碾磨加工品下铅 Pb 0.5 row 拆分 4 条克隆正确注册"""
import os, json, re
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script[^>]*id="inlineData"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1).strip())
tree = data['appendix_a1']['tree']

def norm(s):
    s = (s or '')
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

def pathKey(path):
    return '|'.join([norm(p) for p in path])

def flatten_tree(nodes, path=None):
    if path is None:
        path = []
    result = []
    for n in nodes:
        cur_path = path + [n['name']]
        result.append({'name': n['name'], 'path': cur_path, 'pk': pathKey(cur_path), 'depth': len(cur_path)})
        if n.get('children'):
            result.extend(flatten_tree(n['children'], cur_path))
    return result

all_nodes = flatten_tree(tree)
sidebar_pks = {n['pk']: n for n in all_nodes}

def walk_exact(nodes, path, idx, a1_path, matched_paths):
    if idx >= len(a1_path):
        return
    target = norm(a1_path[idx])
    target_raw = a1_path[idx] or ''
    target_has_brackets = bool(re.search(r'[()（）\[\]【】]', target_raw))
    matched_here = False
    for n in nodes:
        n_name_norm = norm(n['name'])
        matched = n_name_norm == target
        if not matched and idx == len(a1_path) - 1 and not target_has_brackets and len(target) >= 3 and n_name_norm.startswith(target):
            matched = True
        if not matched and idx >= 1:
            sib_core = re.sub(r'[([{【（].*$', '', n['name']).strip()
            sib_core_norm = norm(sib_core)
            if sib_core_norm == target and len(sib_core) > 0 and len(n_name_norm) > len(target):
                matched = True
        if matched:
            matched_here = True
            cur_path = path + [n['name']]
            if idx < len(a1_path) - 1 and n.get('children'):
                walk_exact(n['children'], cur_path, idx + 1, a1_path, matched_paths)
            else:
                matched_paths.append({'pk': pathKey(cur_path), 'path': cur_path})
    if not matched_here and idx == len(a1_path) - 1 and len(path) > 0:
        matched_paths.append({'pk': pathKey(path), 'path': path[:]})


# 找铅污染物
lead = None
for cont in data['contaminants']:
    if cont.get('symbol') == 'Pb':
        lead = cont
        break

print("=" * 70)
print("L2 谷物碾磨加工品 铅 Pb row 全部 item (a1_l1='谷物及其制品' AND a1_l2='谷物碾磨加工品')")
print("=" * 70)

# 找 idx 范围
target_items = []
for i, it in enumerate(lead['items']):
    if (it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）'
        and it.get('a1_l2') == '谷物碾磨加工品'):
        target_items.append((i, it))

print(f"\n找到 {len(target_items)} 条 a1_l2='谷物碾磨加工品' row:")
for i, it in target_items:
    a1_path_raw = [it.get('a1_l1', ''), it.get('a1_l2', ''), it.get('a1_l3', ''), it.get('a1_l4', '')]
    a1_path = [v for v in a1_path_raw if v]
    dedup = []
    for v in a1_path:
        if not dedup or dedup[-1] != v:
            dedup.append(v)
    a1_path = dedup
    matched = []
    walk_exact(tree, [], 0, a1_path, matched)
    actual_pks = [m['pk'] for m in matched]
    in_sidebar = all(pk in sidebar_pks for pk in actual_pks)
    is_l3 = bool(it.get('a1_l3'))
    print(f"\n  [{i}] a1_l3={it.get('a1_l3', '')!r} a1_l4={it.get('a1_l4', '')!r}")
    print(f"      food={it.get('food', '')}")
    print(f"      limit={it.get('limit_value', '')} (克隆={is_l3})")
    print(f"      a1Path: {a1_path}")
    print(f"      注册到 {len(matched)} 个 pk: {actual_pks}")
    print(f"      sidebar 命中: {'OK' if in_sidebar else 'MISSING!'}")

# 检查 L2 谷物碾磨加工品 本级是否还有铅 0.5 row
print("\n" + "=" * 70)
print("L2 谷物碾磨加工品 本级铅 0.5 检查")
print("=" * 70)
mill_l2_pk = '谷物及其制品不包括焙烤制品|谷物碾磨加工品'
mill_l2_items = []
for i, it in enumerate(lead['items']):
    if (it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）'
        and it.get('a1_l2') == '谷物碾磨加工品'
        and it.get('a1_l3', '') == ''):
        a1_path_raw = [it.get('a1_l1', ''), it.get('a1_l2', ''), it.get('a1_l3', ''), it.get('a1_l4', '')]
        a1_path = [v for v in a1_path_raw if v]
        dedup = []
        for v in a1_path:
            if not dedup or dedup[-1] != v:
                dedup.append(v)
        a1_path = dedup
        matched = []
        walk_exact(tree, [], 0, a1_path, matched)
        if any(m['pk'] == mill_l2_pk for m in matched):
            mill_l2_items.append((i, it))

if mill_l2_items:
    print(f"  L2 谷物碾磨加工品 本级仍有 {len(mill_l2_items)} 条铅 0.5 row:")
    for i, it in mill_l2_items:
        print(f"    [{i}] food={it.get('food', '')} limit={it.get('limit_value', '')}")
else:
    print("  ✓ L2 谷物碾磨加工品 本级已无铅 0.5 row (预期效果)")

# 列出 L2 谷物碾磨加工品 下 6 个 L3 的铅 row 数
print("\n" + "=" * 70)
print("L2 谷物碾磨加工品 下 L3 铅 row 分布")
print("=" * 70)
mill_l3_names = ['糙米（包括色稻米）', '大米（粉）', '小麦粉（包括食用麸皮）', '玉米粉、玉米糁（渣）', '麦片', '其他谷物碾磨加工品（例如：小米、高粱米、大麦米、黍米等）']
for l3 in mill_l3_names:
    count = 0
    for i, it in enumerate(lead['items']):
        if (it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）'
            and it.get('a1_l2') == '谷物碾磨加工品'
            and it.get('a1_l3', '') == l3):
            count += 1
    print(f"  {l3}: {count} 条")
