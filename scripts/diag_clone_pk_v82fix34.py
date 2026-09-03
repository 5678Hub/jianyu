# -*- coding: utf-8 -*-
"""检查 8 个汞克隆 row 的 walkExact 注册 pk 与 sidebar flattenTree pk 一致性"""
import os, json, re
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script[^>]*id="inlineData"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1).strip())
tree = data['appendix_a1']['tree']

# 模拟 JS norm()
def norm(s):
    s = (s or '')
    s = re.sub(r'[,，、;；]+', '', s)
    s = re.sub(r'[()（）\[\]【】]+', '', s)
    s = re.sub(r'[:：]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

# 模拟 pathKey
def pathKey(path):
    return '|'.join([norm(p) for p in path])

# 模拟 flattenTree 输出 (sidebar pk)
def flatten_tree(nodes, path=[]):
    """模拟 sidebar flattenTree,返回所有 node 的 pk"""
    result = []
    for n in nodes:
        cur_path = path + [n['name']]
        result.append({
            'name': n['name'],
            'path': cur_path,
            'pk': pathKey(cur_path),
            'depth': len(cur_path)
        })
        if n.get('children'):
            result.extend(flatten_tree(n['children'], cur_path))
    return result

all_nodes = flatten_tree(tree)
print(f"flattenTree 总节点数: {len(all_nodes)}")
print("\n=== L1 谷物及其制品 子树 (前 12 个) ===")
grain_tree_nodes = [n for n in all_nodes if '谷物' in n['name'] or '谷物' in '|'.join(n['path'])][:12]
for n in grain_tree_nodes:
    print(f"  depth={n['depth']} pk={n['pk']}")
    print(f"    name={n['name']} path={n['path']}")

# 模拟 walkExact 注册 8 个克隆
def walk_exact(nodes, path, idx, a1_path, matched_paths):
    """模拟 v82.html walkExact (含 v82-fix34 编辑)"""
    if idx >= len(a1_path):
        return
    target = norm(a1_path[idx])
    target_raw = a1_path[idx] or ''
    target_has_brackets = bool(re.search(r'[()（）\[\]【】]', target_raw))
    matched_here = False
    for n in nodes:
        n_name_norm = norm(n['name'])
        matched = n_name_norm == target
        # v82-fix34
        if idx == 0 and not matched and n.get('children') and len(path) <= 1:
            walk_exact(n['children'], path + [n['name']], idx + 1, a1_path, matched_paths)
            continue
        # fallback A
        if not matched and idx == len(a1_path) - 1 and not target_has_brackets and len(target) >= 3 and n_name_norm.startswith(target):
            matched = True
        # core match
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

# 找汞污染物
for cont in data['contaminants']:
    if '汞' not in cont.get('contaminant', ''):
        continue
    print(f"\n=== 汞污染物 items[12..19] (8 个克隆) walkExact 模拟 ===")
    for i in [12, 13, 14, 15, 16, 17, 18, 19]:
        item = cont['items'][i]
        a1_path_raw = [item.get('a1_l1',''), item.get('a1_l2',''), item.get('a1_l3',''), item.get('a1_l4','')]
        a1_path = [v for v in a1_path_raw if v]
        # 去连续重复
        dedup = []
        for v in a1_path:
            if not dedup or dedup[-1] != v:
                dedup.append(v)
        a1_path = dedup
        
        matched = []
        walk_exact(tree, [], 0, a1_path, matched)
        print(f"\n  [{i}] a1_l3={item.get('a1_l3','')!r} a1_l4={item.get('a1_l4','')!r}")
        print(f"      a1Path={a1_path}")
        print(f"      注册到 {len(matched)} 个 pk:")
        for m in matched:
            # 检查 pk 是否在 sidebar 节点中
            in_sidebar = any(n['pk'] == m['pk'] for n in all_nodes)
            mark = "✓" if in_sidebar else "✗ 不在 sidebar!"
            print(f"        pk={m['pk']!r}  {mark}")
    break
