"""扫描所有污染物 row，找出「除外」列表涉及的 L3 节点 + 检查 own row 缺失情况"""
import re, json
with open(r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'<script type="application/json" id="inlineData">', c)
s = m.end()
depth = 0; in_str = False; esc = False; i = s
while i < len(c):
    ch = c[i]
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
    else:
        if ch == '"': in_str = True
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: e = i + 1; break
    i += 1
data = json.loads(c[s:e])

tree = data['appendix_a1']['tree']

# 1) 收集 A.1 树所有 L3 节点名（递归）
def walk_l3(nodes, path, depth_target=3):
    res = []
    for n in nodes:
        cur_path = path + [n['name']]
        if len(cur_path) == depth_target:
            res.append(cur_path)
        if n.get('children') and len(cur_path) < depth_target:
            res.extend(walk_l3(n['children'], cur_path, depth_target))
    return res

l3_paths = walk_l3(tree, [], 3)
print(f'A.1 树共有 {len(l3_paths)} 个 L3 节点')
for p in l3_paths:
    print(f'  L3: {" > ".join(p)}')

# 2) 收集所有「除外」列表中的具体子类名（来自 row food）
print('\n\n所有 row food 含「除外」列表的：')
exclude_items_per_table = {}
for t in data['contaminants']:
    sym = t.get('symbol', '')
    for idx, it in enumerate(t['items']):
        food = it.get('food', '')
        if '除外' in food:
            # 提取「除外」前面「〔...〕」括号内容
            m_ex = re.search(r'[\[〔\(（]([^\]〕\)）]+)除外', food)
            if m_ex:
                excl_text = m_ex.group(1)
                # 按「、」拆分
                excl_list = re.split(r'[、，,]+', excl_text)
                excl_list = [e.strip() for e in excl_list if e.strip()]
                a1_l2 = it.get('a1_l2', '')
                a1_l3 = it.get('a1_l3', '')
                a1_l4 = it.get('a1_l4', '')
                limit = it.get('limit_value', '') or it.get('limit', '')
                print(f'  [{sym}] idx={idx} a1l2={a1_l2[:18]} a1l3={a1_l3[:18]} food={food[:60]} limit={limit}')
                print(f'    除外列表: {excl_list}')
                # 记录到映射
                for excl_name in excl_list:
                    exclude_items_per_table.setdefault(sym, {}).setdefault(a1_l2, []).append({
                        'idx': idx, 'excl_name': excl_name, 'limit': limit
                    })

# 3) 对比 A.1 树中每个 L3 节点是否在「除外」列表中出现过（即 PDF 中是否有专属 row）
print('\n\n===== 扫描结果：哪些 L3 节点在 PDF 中被「除外」提到，可能需要专属 row =====')
# 收集所有被「除外」提到的具体子类名
all_excl_names = set()
for sym, l2_dict in exclude_items_per_table.items():
    for l2, lst in l2_dict.items():
        for e in lst:
            all_excl_names.add(e['excl_name'])

print(f'\n所有「除外」列表中出现过的具体食品名 ({len(all_excl_names)} 个):')
for n in sorted(all_excl_names):
    # 检查 A.1 树 L3 节点
    l3_match = [p for p in l3_paths if n in p[-1] or any(n in x for x in p)]
    if l3_match:
        print(f'  {n}: A.1 树 L3 节点匹配: {l3_match}')
    else:
        print(f'  {n}: ⚠️ A.1 树无 L3 节点匹配（可能在 L3 节点括号示例中）')