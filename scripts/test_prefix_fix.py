"""
Debug: walkExact prefix-match bug
The '末层 fallback A' 简写匹配 should ONLY match when tree node has brackets,
not when target (a1_lN) is shorter because of its own brackets.

Test case:
  a1_l3='果蔬汁（浆）' (norm='果蔬汁浆')
  tree L3='果蔬汁（浆）类饮料' (norm='果蔬汁浆类饮料')
  → nname.startsWith(target)=TRUE, but should be FALSE (no brackets in tree node)

Fix: also require n.name (raw) has brackets/parens/[]/{}/【】 before prefix match.
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

def walk_exact_v2(a1path, tree):
    """修复版: prefix match 只在 target (a1_lN 原始字符串) 不含括号时触发
    例:
      target_raw='果蔬汁（浆）'(含括号) + nname='果蔬汁（浆）类饮料' → 跳过 prefix match
        否则 target.norm='果蔬汁浆' 是 nname.norm='果蔬汁浆类饮料' 的前缀,误匹配。
      target_raw='肉食性鱼类'(无括号) + nname='肉食性鱼类（例如:...）' → 允许 prefix match
        原 fallback A 行为不变。
    """
    if not a1path: return []
    matched_paths = []
    def _walk(nodes, path, idx):
        if idx >= len(a1path): return
        target = norm(a1path[idx])
        target_raw = a1path[idx]
        matched_here = False
        for n in nodes:
            nname = norm(n['name'])
            matched = (nname == target)
            # 末层 fallback A: 简写匹配全称 (修复: target 原始字符串不能含括号)
            #   target 含括号时,norm 后变短,极易误匹配到 nname 的真前缀
            if (not matched and idx == len(a1path) - 1
                    and len(target) >= 3
                    and nname.startswith(target)
                    and not has_brackets(target_raw)):
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

# 重新验证 L3 果蔬汁（浆）类饮料
target_l3_guozhi = None
for n in tree:
    if n['name'] == '饮料类':
        for c2 in n.get('children', []):
            if '果蔬汁类及其饮料' in c2['name']:
                for c3 in c2.get('children', []):
                    if '果蔬汁（浆）类饮料' in c3['name']:
                        target_l3_guozhi = [n['name'], c2['name'], c3['name']]

candidates = []
for c in DATA['contaminants']:
    for it in c.get('items', []):
        if it.get('food') in ('葡萄汁', '浓缩果蔬汁(浆)'):
            candidates.append((c['table_no'], it))

print('=== v2 修复后: walkExact 注册 ===')
for tn, r in candidates:
    ap = [r.get('a1_l1'), r.get('a1_l2'), r.get('a1_l3'), r.get('a1_l4')]
    ap = [x for x in ap if x]
    dedup = []
    for i, v in enumerate(ap):
        if i == 0 or v != ap[i-1]:
            dedup.append(v)
    paths = walk_exact_v2(dedup, tree)
    print(f'\nrow food={r["food"]!r} limit={r["limit_value"]}')
    for p in paths:
        marker = ' ← ← 命中 target_l3_guozhi!' if p == target_l3_guozhi else ''
        print(f'  - {p}{marker}')
