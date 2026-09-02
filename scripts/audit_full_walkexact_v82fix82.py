#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82 整体扫描 - 完整 walkExact 模拟"""
import re, json
from pathlib import Path

src = Path(r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html').read_text(encoding='utf-8')
m = re.search(r'<script type="application/json" id="inlineData">', src)
i = m.end(); depth = 0; start = i; end_idx = i
src_text = src
while i < len(src_text):
    if src_text[i] == '{': depth += 1
    elif src_text[i] == '}':
        depth -= 1
        if depth == 0: end_idx = i + 1; break
    i += 1
data = json.loads(src_text[start:end_idx])
tree = data['appendix_a1']['tree']
contaminants = data['contaminants']

# 完整模拟 matchItemToPaths
def norm(s):
    s = s or ''
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

def pathKey(path):
    nf = lambda s: (s or '').replace('|', '||')
    return '|'.join(nf(p) for p in path)

def matchItemToPaths(item, tree):
    a1PathRaw = [item.get('a1_l1',''), item.get('a1_l2',''), item.get('a1_l3',''), item.get('a1_l4','')]
    a1PathRaw = [v for v in a1PathRaw if v]
    a1PathRaw = [v for i, v in enumerate(a1PathRaw) if i == 0 or v != a1PathRaw[i-1]]
    matchedPaths = []

    if not a1PathRaw:
        if item.get('food'):
            foodNorm = norm(item['food'])
            foodCore = re.sub(r'[\(\[【（].*$', '', str(item['food'])).strip()
            foodCoreNorm = norm(foodCore)
            def find_food(nodes, curPath):
                for n in nodes:
                    if norm(n['name']) == foodNorm or norm(n['name']) == foodCoreNorm:
                        curPath = curPath + [n['name']]
                        if n.get('children'):
                            deepest = curPath[:]
                            def go_deep(ns, cp):
                                nonlocal deepest
                                for nn in ns:
                                    if nn.get('children'):
                                        go_deep(nn['children'], cp + [nn['name']])
                                    else:
                                        deepest = cp + [nn['name']]
                            go_deep(n['children'], curPath)
                            matchedPaths.append({'pk': pathKey(deepest), 'path': deepest})
                            return
                    if n.get('children'):
                        find_food(n['children'], curPath)
            find_food(tree, [])
        return matchedPaths

    def walkExact(nodes, path, idx):
        nonlocal matchedPaths
        if idx >= len(a1PathRaw): return
        target = norm(a1PathRaw[idx])
        targetRaw = a1PathRaw[idx]
        targetHasBrackets = bool(re.search(r'[()（）\[\]【】]', targetRaw))
        matchedHere = False
        for n in nodes:
            nNameNorm = norm(n['name'])
            matched = nNameNorm == target
            if not matched and idx == len(a1PathRaw) - 1 and not targetHasBrackets and len(target) >= 3 and nNameNorm.startswith(target):
                matched = True
            if not matched and idx >= 1:
                sibCore = re.sub(r'[\(\[【（].*$', '', n['name']).strip()
                sibCoreNorm = norm(sibCore)
                if sibCoreNorm == target and len(sibCore) > 0 and len(nNameNorm) > len(target):
                    matched = True
            if matched:
                matchedHere = True
                curPath = path + [n['name']]
                if idx < len(a1PathRaw) - 1 and n.get('children'):
                    walkExact(n['children'], curPath, idx + 1)
                else:
                    matchedPaths.append({'pk': pathKey(curPath), 'path': curPath})
        if not matchedHere and idx == len(a1PathRaw) - 1 and len(path) > 0:
            matchedPaths.append({'pk': pathKey(path), 'path': path[:]})

    walkExact(tree, [], 0)
    return matchedPaths

# row 注册
row_register = {}
for c in contaminants:
    for idx, it in enumerate(c.get('items', [])):
        for m in matchItemToPaths(it, tree):
            row_register.setdefault(m['pk'], []).append({'contam': c['contaminant'], 'idx': idx, 'item': it})

# 收集 L3/L4 节点 pk
by_l1 = {}
def collect(node, path):
    new_path = path + [node['name']]
    if len(new_path) >= 4:  # L3 节点: [L1, L2, L3]
        l1 = new_path[0]
        cur_pk = pathKey(new_path)
        has_own = len(row_register.get(cur_pk, [])) > 0
        by_l1.setdefault(l1, []).append({'pk': cur_pk, 'path': new_path, 'level': len(new_path), 'has_own': has_own, 'own_count': len(row_register.get(cur_pk, []))})
    for c in node.get('children', []):
        collect(c, new_path)
for root in tree:
    collect(root, [])

print('【各 L1 章节 idx 空 L3/L4 节点 + own row 数 (完整 walkExact 模拟)】')
print()
total_empty = 0
for l1, items in sorted(by_l1.items(), key=lambda x: -len([i for i in x[1] if not i['has_own']])):
    empties = [i for i in items if not i['has_own']]
    if not empties: continue
    total_empty += len(empties)
    print(f'\n--- {l1[:30]} ({len(empties)} 个) ---')
    for i in sorted(empties, key=lambda x: x['path']):
        print(f'  {"→".join(i["path"][1:])}')

# Debug: 肉及肉制品 全部 L3/L4 节点
print()
print('=== Debug: 肉及肉制品 全部 L3/L4 节点 + own row 数 ===')
for i in by_l1.get('肉及肉制品', []):
    mark = '✅有' if i['has_own'] else '❌空'
    print(f'  {mark} | L{i["level"]} | {"→".join(i["path"][1:])}')

print()
print(f'肉及肉制品 by_l1 总节点数: {len(by_l1.get("肉及肉制品", []))}')
print(f'\n总 idx 空 L3/L4: {total_empty}')