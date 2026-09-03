import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

tree = data['appendix_a1']['tree']

# 列出 tree 中所有顶层 L1 节点名
print('=== Tree 顶层 ===')
for n in tree:
    print(f'  {n["name"]}')

# 列出部分需要核对的 L2 名
def find_l1_children(l1_name):
    for n in tree:
        if n['name'] == l1_name:
            print(f'\n=== {l1_name} children ===')
            for c in n.get('children', []):
                print(f'  {c["name"]}')

# 关键 L2 在 tree 中的真实名
for l1 in ['动物性水产及其制品', '植物性水产及其制品', '肉及肉制品', '谷物及其制品', '酒类']:
    find_l1_children(l1)

# 关键 L2 名:
print()
print('=== 检查关键 L2 是否在 tree 中 ===')
for l2 in ['动物油脂（例如：猪油、牛油、鱼油、磷虾油等）', '动物油脂(例如:猪油、牛油、鱼油、磷虾油等)',
          '发酵酒（例如：葡萄酒、黄酒、果酒、啤酒等）', '发酵酒(例如:葡萄酒、黄酒、果酒、啤酒等)',
          '肉制品（包括内脏制品、血制品）', '肉制品(包括内脏制品、血制品)',
          '肉类(生鲜肉、冷却肉、冷冻肉等)', '肉类（生鲜肉、冷却肉、冷冻肉等）']:
    def check(nodes):
        for n in nodes:
            if n['name'] == l2: return True
            if n.get('children'):
                if check(n['children']): return True
        return False
    print(f'  {check(tree)} | {l2}')