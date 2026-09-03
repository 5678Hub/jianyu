import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

tree = data['appendix_a1']['tree']

def find_node(nodes, target_name):
    for n in nodes:
        if n['name'] == target_name: return n
        if n.get('children'):
            r = find_node(n['children'], target_name)
            if r: return r
    return None

def get_l2_children(l2_name):
    node = find_node(tree, l2_name)
    if not node: return []
    return [c['name'] for c in node.get('children', [])]

# 列出所有 inlineData 的 row，按 (a1_l2, a1_l3, a1_l4) 分组
from collections import defaultdict
rows_by_path = defaultdict(list)
for c in data['contaminants']:
    for idx, it in enumerate(c.get('items', [])):
        a1l2 = it.get('a1_l2', '')
        a1l3 = it.get('a1_l3', '')
        a1l4 = it.get('a1_l4', '')
        if not a1l2 and not a1l3:
            continue
        key = (a1l2, a1l3, a1l4)
        rows_by_path[key].append((c['contaminant'], idx, it.get('food','')[:50], it.get('limit_value')))

# 列出 (a1_l2, a1_l3) 在 tree 中 a1_l3 不存在的 row
print('=== a1_l3 在 tree 中找不到的 row 列表 ===')
print('（按 a1_l2 / a1_l3 分组，显示现有 a1_l 路径 + 建议修正方案）')
print()
for (a1l2, a1l3, a1l4), items in sorted(rows_by_path.items()):
    if not a1l3:
        continue
    l2_node = find_node(tree, a1l2)
    if not l2_node:
        print(f"\n[L2={a1l2}] 不在 tree 中! （{len(items)} 条 row）")
        for c, idx, food, limit in items[:3]:
            print(f"   {c}: food={food} | limit={limit}")
        continue
    children_names = [c['name'] for c in l2_node.get('children', [])]
    children_cores = [re.sub(r'[([{【（].*$', '', n).strip() for n in children_names]
    if a1l3 not in children_names and a1l3 not in children_cores:
        # 缺失节点
        # 看看是否能找到同名但不同的节点（说明是标点不一致）
        sim = [n for n in children_names if re.sub(r'[()（）\[\]【】,，:：\s]', '', n) == re.sub(r'[()（）\[\]【】,，:：\s]', '', a1l3)]
        sim_msg = f"  相似节点: {sim[:3]}" if sim else ""
        print(f"\n[L2={a1l2}] L3={a1l3} 缺失 ({len(items)} 条){sim_msg}")
        # 列出可能的修正
        for c, idx, food, limit in items[:5]:
            print(f"   {c}: food={food} | limit={limit} | a1_l3='{a1l3}'")
        if len(items) > 5:
            print(f"   ... 还有 {len(items) - 5} 条")