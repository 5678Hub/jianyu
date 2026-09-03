import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

# 直接查 '水产制品' 节点下的 children 名
tree = data['appendix_a1']['tree']
def find_node(nodes, target_name):
    for n in nodes:
        if n.get('name') == target_name: return n
        if n.get('children'):
            r = find_node(n['children'], target_name)
            if r: return r
    return None

# 查 '水产动物及其制品' 节点
node = find_node(tree, '水产动物及其制品')
print(f"水产动物及其制品 children:")
for c in node.get('children', []):
    print(f"  - {c.get('name')}")

# 查 '水产制品' 节点
node2 = find_node(tree, '水产制品')
print(f"\n水产制品 children:")
for c in node2.get('children', []):
    print(f"  - {c.get('name')}")

# 查 '鱼类' 节点
node3 = find_node(tree, '鱼类')
print(f"\n鱼类 children:")
for c in node3.get('children', []):
    print(f"  - {c.get('name')}")