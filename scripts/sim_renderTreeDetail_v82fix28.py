import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data_json = m.group(1)

# 复制 sim_matchItem 后的 idx 构建代码（直接 import 函数）
import sys
sys.path.insert(0, 'scripts')
import importlib.util
spec = importlib.util.spec_from_file_location("sim_match", "scripts/sim_matchItem_v82fix28.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
itemIndex = mod.itemIndex
tree = mod.tree

def pathKey(path):
    return '|'.join(path)

def aggregateUpwards(nodePath):
    seen = {}
    excluded = []
    for i in range(len(nodePath) - 1, -1, -1):
        ancestorPath = nodePath[:i + 1]
        ancestorKey = pathKey(ancestorPath)
        if ancestorKey not in itemIndex: continue
        ancestorName = nodePath[i]
        rawItems = itemIndex[ancestorKey]
        # isApplicableToPath 简化版（外层没有任何"除外"的 row）
        filtered = rawItems
        if len(filtered) == 0:
            if len(rawItems) > 0: excluded.append((ancestorName, len(rawItems)))
            continue
        for x in filtered:
            dedupK = f"{x.get('_table_no','')}|{x.get('food','')}|{x.get('limit_value','')}|{x.get('sub_value','')}"
            enriched = dict(x, _viaSub=ancestorName, _depth=i + 1)
            existing = seen.get(dedupK)
            if not existing or enriched['_depth'] > existing['_depth']:
                seen[dedupK] = enriched
    items = sorted(seen.values(), key=lambda x: x['_depth'])
    return items, excluded

# 模拟查询 非肉食性鱼类
path = ['水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类']
items, excluded = aggregateUpwards(path[:3])
print(f"=== 查询 path={path} ===")
print(f"非肉食性鱼类 idx own: {len(itemIndex.get(pathKey(path), []))}")
print(f"primaryLevel='上一级', 引用 鱼类 (path={path[:3]})")
print(f"aggregateUpwards 返回 {len(items)} 条:")
for it in items:
    a1 = '|'.join([it.get(f'a1_l{i}', '') for i in range(1, 5)])
    print(f"  [{it.get('_contaminant','?')}] food={it.get('food','')[:50]:<50} a1=[{a1}] limit={it.get('limit_value','?')} _via={it.get('_viaSub')} _depth={it.get('_depth')}")

print()
print('--- 模拟查询 鱼糜制品 (catid=137) ---')
path2 = ['水产动物及其制品', '水产制品', '鱼糜制品（例如：鱼丸等）']
print(f"鱼糜制品 idx own: {len(itemIndex.get(pathKey(path2), []))}")
# primary fallback
primaryDepth = None
for d in range(len(path2), 0, -1):
    if pathKey(path2[:d]) in itemIndex:
        primaryDepth = d
        break
print(f"primaryDepth = {primaryDepth} → primary 引用 {path2[:primaryDepth]}")
items, exc = aggregateUpwards(path2[:primaryDepth])
print(f"返回 {len(items)} 条:")
for it in items:
    a1 = '|'.join([it.get(f'a1_l{i}', '') for i in range(1, 5)])
    print(f"  [{it.get('_contaminant','?')}] food={it.get('food','')[:50]:<50} a1=[{a1}] limit={it.get('limit_value','?')} _via={it.get('_viaSub')} _depth={it.get('_depth')}")