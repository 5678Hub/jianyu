"""
模拟 v82-fix26 的 matchItemToPaths 行为,分析花生 (镉 ≤0.5) 的归属。
"""
import re, json

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 inlineData
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

a1 = data['appendix_a1']
tree = a1['tree']

# ---- 移植 matchItemToPaths 逻辑 ----
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
    best_path = None
    for n in nodes:
        nn = norm(n.name)
        if nn == food_norm or nn == food_core_norm:
            # 找最深同名
            deepest = None
            def go_deeper(nn2, p):
                nonlocal deepest
                if not nn2.get('children'):
                    deepest = p
                    return
                for c in nn2['children']:
                    cn = norm(c['name'])
                    if cn == food_core_norm or cn.startswith(food_core_norm) or (len(food_core_norm) >= 3 and food_core_norm in cn):
                        go_deeper(c, p + [c['name']])
            go_deeper(n, cur_path + [n['name']])
            if deepest:
                if not best_path or len(deepest) > len(best_path):
                    best_path = deepest
            elif not best_path:
                best_path = cur_path + [n['name']]
        if n.get('children'):
            sub = walk_food(n['children'], food_norm, food_core_norm, cur_path + [n['name']])
            if sub and (not best_path or len(sub) > len(best_path)):
                best_path = sub
    return best_path

def match_item_to_paths(item, tree):
    """Port of matchItemToPaths"""
    # 1) a1_l1/l2/l3/l4 精确路径
    a1_path_raw = []
    last = None
    for v in [item.get('a1_l1',''), item.get('a1_l2',''), item.get('a1_l3',''), item.get('a1_l4','')]:
        if v and v != last:
            a1_path_raw.append(v)
            last = v
    a1_path = list(a1_path_raw)
    if a1_path and is_footnote(a1_path[-1]) and item.get('food'):
        # 在 tree 中找 food 同名节点
        found = False
        def probe(nodes):
            nonlocal found
            for n in nodes:
                if norm(n['name']) == norm(item['food']):
                    found = True; return
                if n.get('children'):
                    probe(n['children'])
        probe(tree)
        if found:
            a1_path[-1] = item['food']
        else:
            a1_path.pop()
    matched_paths = []
    if a1_path:
        def walk_exact(nodes, path, idx):
            if idx >= len(a1_path): return
            target = norm(a1_path[idx])
            target_raw = a1_path[idx]
            target_has_brackets = bool(re.search(r'[()（）\[\]【】]', target_raw))
            matched_here = False
            for n in nodes:
                nname_norm = norm(n['name'])
                matched = nname_norm == target
                if not matched and idx == len(a1_path) - 1 and not target_has_brackets \
                    and len(target) >= 3 and nname_norm.startswith(target):
                    matched = True
                if not matched and idx >= 1:
                    sib_core = re.sub(r'[([{【（].*$', '', n['name']).strip()
                    sib_core_norm = norm(sib_core)
                    if sib_core_norm == target and len(sib_core) > 0 and len(nname_norm) > len(target):
                        matched = True
                if matched:
                    matched_here = True
                    cur_path = path + [n['name']]
                    if idx < len(a1_path) - 1 and n.get('children'):
                        walk_exact(n['children'], cur_path, idx + 1)
                    else:
                        matched_paths.append({'pk': '|'.join(cur_path), 'path': cur_path})
            if not matched_here and idx == len(a1_path) - 1 and len(path) > 0:
                matched_paths.append({'pk': '|'.join(path), 'path': list(path)})
        walk_exact(tree, [], 0)

    if not matched_paths and item.get('food'):
        food_norm = norm(item['food'])
        food_core = re.sub(r'[([{【（].*$', '', item['food']).strip()
        food_core_norm = norm(food_core)
        best_path = walk_food(tree, food_norm, food_core_norm, [])
        if best_path:
            matched_paths.append({'pk': '|'.join(best_path), 'path': best_path})

    return matched_paths


# ---- 测试 ----
# 提取 3 个相关 item
items_to_test = []
for contam in data['contaminants']:
    for it in contam.get('items', []):
        if it.get('a1_l1', '') == '坚果及籽类':
            items_to_test.append({
                '污染': contam['contaminant'],
                'food': it['food'],
                'limit': it['limit_value'],
                'a1_l1': it.get('a1_l1',''),
                'a1_l2': it.get('a1_l2',''),
                'a1_l3': it.get('a1_l3',''),
                'a1_l4': it.get('a1_l4',''),
                'note': it.get('note','')
            })

print('=' * 80)
print('当前 v82-fix26 对 3 个坚果及籽类 item 的归属')
print('=' * 80)
for it in items_to_test:
    res = match_item_to_paths(it, tree)
    print(f"\n{it['污染']} ≤{it['limit']} - food='{it['food']}' note='{it['note']}'")
    print(f"  a1_l: '{it['a1_l1']}' / '{it['a1_l2']}' / '{it['a1_l3']}' / '{it['a1_l4']}'")
    print(f"  → 注册到: {len(res)} 处")
    for r in res:
        print(f"     - {' > '.join(r['path'])}")