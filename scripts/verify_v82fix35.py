# -*- coding: utf-8 -*-
"""验证 v82-fix35: 8 个汞克隆 walkExact 注册 (无 v82-fix34 编辑) 全部命中正确 L3 pk"""
import os, json, re
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script[^>]*id="inlineData"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1).strip())
tree = data['appendix_a1']['tree']

# 模拟 JS norm() (与 v82.html line 1063-1069 一致)
def norm(s):
    s = (s or '')
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

def pathKey(path):
    return '|'.join([norm(p) for p in path])

# 模拟 sidebar flattenTree 输出
def flatten_tree(nodes, path=None):
    if path is None:
        path = []
    result = []
    for n in nodes:
        cur_path = path + [n['name']]
        result.append({
            'name': n['name'],
            'path': cur_path,
            'pk': pathKey(cur_path),
            'depth': len(cur_path),
        })
        if n.get('children'):
            result.extend(flatten_tree(n['children'], cur_path))
    return result

all_nodes = flatten_tree(tree)
sidebar_pks = {n['pk']: n for n in all_nodes}

# walkExact 模拟 (NO v82-fix34 edit,原版逻辑)
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
        # NO v82-fix34 edit (已回滚)
        # Fallback A: 末层简写匹配全称 (target.length >= 3 且不含括号)
        if not matched and idx == len(a1_path) - 1 and not target_has_brackets and len(target) >= 3 and n_name_norm.startswith(target):
            matched = True
        # Core match: target 简写 vs tree 全称 (括号前部分)
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
    # Fallback B
    if not matched_here and idx == len(a1_path) - 1 and len(path) > 0:
        matched_paths.append({'pk': pathKey(path), 'path': path[:]})


print("=" * 70)
print("验证 8 个汞克隆 (idx 12-19) walkExact 注册结果")
print("=" * 70)

# 找汞污染物
mercury = None
for cont in data['contaminants']:
    if cont.get('contaminant') in ('汞', '总汞'):
        mercury = cont
        break

expected = {
    12: '谷物及其制品不包括焙烤制品|谷物|稻谷',          # 稻谷
    13: '谷物及其制品不包括焙烤制品|谷物|玉米',          # 玉米
    14: '谷物及其制品不包括焙烤制品|谷物|小麦',          # 小麦
    15: '谷物及其制品不包括焙烤制品|谷物碾磨加工品|糙米包括色稻米',  # 糙米
    16: '谷物及其制品不包括焙烤制品|谷物碾磨加工品|大米粉',          # 大米粉
    17: '谷物及其制品不包括焙烤制品|谷物碾磨加工品|小麦粉包括食用麸皮',  # 小麦粉
    18: '谷物及其制品不包括焙烤制品|谷物碾磨加工品|玉米粉玉米糁渣',     # 玉米粉玉米糁渣 (玉米粉食品)
    19: '谷物及其制品不包括焙烤制品|谷物碾磨加工品|玉米粉玉米糁渣',     # 玉米粉玉米糁渣 (玉米糁渣食品)
}

all_pass = True
for i in range(12, 20):
    item = mercury['items'][i]
    a1_path_raw = [item.get('a1_l1', ''), item.get('a1_l2', ''), item.get('a1_l3', ''), item.get('a1_l4', '')]
    a1_path = [v for v in a1_path_raw if v]
    dedup = []
    for v in a1_path:
        if not dedup or dedup[-1] != v:
            dedup.append(v)
    a1_path = dedup

    matched = []
    walk_exact(tree, [], 0, a1_path, matched)

    exp_pk = expected[i]
    actual_pks = [m['pk'] for m in matched]
    in_sidebar = all(pk in sidebar_pks for pk in actual_pks)
    matched_exp = exp_pk in actual_pks

    status = '✓' if (matched_exp and in_sidebar and len(matched) == 1) else '✗'
    if status == '✗':
        all_pass = False
    print(f"\n[{i}] a1_l2={item.get('a1_l2','')!r} a1_l3={item.get('a1_l3','')!r} a1_l4={item.get('a1_l4','')!r}")
    print(f"    a1Path: {a1_path}")
    print(f"    注册到 {len(matched)} 个 pk: {actual_pks}")
    print(f"    期望 pk: {exp_pk}")
    print(f"    sidebar 命中: {'OK' if in_sidebar else 'MISSING!'}")
    print(f"    匹配期望 pk: {'OK' if matched_exp else 'NO!'}")
    print(f"    状态: {status}")

print("\n" + "=" * 70)
print(f"总结: {'全部通过 ✓' if all_pass else '存在问题 ✗'}")
print("=" * 70)

# 同时验证 sidebar 计数 (稻谷 L3 应有 1 个汞克隆)
print("\n=== sidebar 计数预览 (谷物 L1 子树) ===")
grain_l1_node = next((n for n in all_nodes if n['depth'] == 1 and '谷物' in n['name']), None)
if grain_l1_node:
    print(f"L1: {grain_l1_node['name']}")
    # 找 L1 下的所有 L2/L3
    for n in all_nodes:
        if n['depth'] >= 2 and n['path'][0] == grain_l1_node['name']:
            indent = '  ' * (n['depth'] - 1)
            # 数在该 pk 注册了多少汞 row
            count = 0
            for j in range(12, 20):
                item = mercury['items'][j]
                a1_path_raw = [item.get('a1_l1', ''), item.get('a1_l2', ''), item.get('a1_l3', ''), item.get('a1_l4', '')]
                a1_path = [v for v in a1_path_raw if v]
                dedup = []
                for v in a1_path:
                    if not dedup or dedup[-1] != v:
                        dedup.append(v)
                a1_path = dedup
                matched = []
                walk_exact(tree, [], 0, a1_path, matched)
                if any(m['pk'] == n['pk'] for m in matched):
                    count += 1
            print(f"{indent}{n['name']} (汞克隆数={count})")
