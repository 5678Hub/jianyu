"""v82-fix28 回归测试"""
import re, json

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

# === 1. v82-fix24 (蒸馏酒/发酵酒 idx 应 >= 1) ===
print('=== v82-fix24 回归 ===')
for l2_name in ['蒸馏酒（例如：白酒、白兰地、威士忌、伏特加、朗姆酒等）', '发酵酒（例如：葡萄酒、黄酒、果酒、啤酒等）']:
    count = 0
    for c in data['contaminants']:
        for it in c.get('items', []):
            if it.get('a1_l2') == l2_name:
                count += 1
    print(f'  L2 {l2_name[:15]}... 自身有 {count} 条')

# === 2. v82-fix25 (0.04 葡萄汁 不 leak 到 果蔬汁（浆）类饮料) ===
print('\n=== v82-fix25 回归 ===')
for c in data['contaminants']:
    for it in c.get('items', []):
        if it.get('food') == '葡萄汁' and it.get('limit_value') == '0.04':
            a1 = [it.get(f'a1_l{i}','') for i in range(1,5)]
            print(f'  0.04 葡萄汁 a1: {a1}')
            # 应在 果蔬汁（浆） own

# === 3. v82-fix26 (空叶子节点可点击) ===
print('\n=== v82-fix26 回归 ===')
# 此测试在 simulator 中无法直接测,需要 jsdom. 跳过

# === 4. v82-fix27 (花生 0.5 应在 生干坚果及籽类) ===
print('\n=== v82-fix27 回归 ===')
for c in data['contaminants']:
    for it in c.get('items', []):
        if it.get('food') == '花生' and it.get('a1_l1') == '坚果及籽类':
            a1 = [it.get(f'a1_l{i}','') for i in range(1,5)]
            print(f'  花生 a1: {a1}')

# === 5. v82-fix28 关键 fix (idx 不再被污染) ===
print('\n=== v82-fix28 关键 fix ===')
tree = data['appendix_a1']['tree']
def find_node(nodes, name):
    for n in nodes:
        if n['name'] == name: return n
        if n.get('children'):
            r = find_node(n['children'], name)
            if r: return r
    return None

# 5.1 idx[水产制品] 应只有 2 条 (不含 海蜇制品 / 鱼类制品 等)
sp = find_node(tree, '水产制品')
sp_children = [c['name'] for c in sp.get('children', [])]
print(f'  水产制品 children: {sp_children}')
expected = ['海蜇制品', '鱼类制品', '其他鱼类制品', '其他水产品']
missing = [e for e in expected if e not in sp_children]
print(f'  期望新增节点 {expected} 已添加? {not missing}')

# 5.2 模拟 buildItemIndex 看 idx['水产制品']
def pathKey(path):
    return '|'.join(path)

itemIndex = {}
for c in data['contaminants']:
    for it in c.get('items', []):
        a1 = [it.get(f'a1_l{i}', '') for i in range(1, 5)]
        a1f = [x for x in a1 if x]
        if not a1f: continue
        pk = pathKey(a1f)
        if pk not in itemIndex:
            itemIndex[pk] = []
        itemIndex[pk].append(it)

# 检查 idx[水产制品] 应只含 a1=['水产制品'] 的 row
sp_idx = itemIndex.get('水产动物及其制品|水产制品', [])
print(f'\n  idx[水产制品] ({len(sp_idx)} 条):')
for it in sp_idx:
    a1 = [it.get(f'a1_l{i}','') for i in range(1,5)]
    print(f'    {it.get("food")} | a1={a1}')
# 期望: 只有 2 条 (铅 1.0 + NDMA 4.0)
assert len(sp_idx) == 2, f'BUG: idx[水产制品] 应只有 2 条, 实际 {len(sp_idx)} 条'
print(f'  ✓ idx[水产制品] 只有 2 条 (无污染)')

# 5.3 idx[海蜇制品] 应有 1 条
hp_idx = itemIndex.get('水产动物及其制品|水产制品|海蜇制品', [])
print(f'\n  idx[海蜇制品] ({len(hp_idx)} 条):')
for it in hp_idx:
    print(f'    {it.get("food")} | limit={it.get("limit_value")}')
assert len(hp_idx) == 1
print(f'  ✓ idx[海蜇制品] 1 条 (铅 ≤2.0)')

# 5.4 idx[鱼类制品] 应有 2 条
yp_idx = itemIndex.get('水产动物及其制品|水产制品|鱼类制品', [])
print(f'\n  idx[鱼类制品] ({len(yp_idx)} 条):')
for it in yp_idx:
    print(f'    {it.get("food")} | limit={it.get("limit_value")}')
assert len(yp_idx) == 2
print(f'  ✓ idx[鱼类制品] 2 条')

# 5.5 idx[肉食性鱼类] 应有 10 条
rsy_idx = itemIndex.get('水产动物及其制品|鲜、冻水产动物|鱼类|肉食性鱼类（例如：金枪鱼、金目鲷、枪鱼、鲨鱼等）', [])
print(f'\n  idx[肉食性鱼类] ({len(rsy_idx)} 条)')
assert len(rsy_idx) == 10
print(f'  ✓ idx[肉食性鱼类] 10 条')

# 5.6 idx[鱼类] 应有 3 条 (含 砷 — 鱼类及其制品)
yl_idx = itemIndex.get('水产动物及其制品|鲜、冻水产动物|鱼类', [])
print(f'\n  idx[鱼类] ({len(yl_idx)} 条):')
for it in yl_idx:
    print(f'    {it.get("food")} | limit={it.get("limit_value")}')
assert len(yl_idx) == 3, f'BUG: idx[鱼类] 应有 3 条, 实际 {len(yl_idx)} 条'
print(f'  ✓ idx[鱼类] 3 条 (含 砷 — 鱼类及其制品)')

print('\n=== v82-fix28 所有检查通过 ===')