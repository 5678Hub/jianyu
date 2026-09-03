"""
模拟花生在 GB 2762-2025 标准下的归属(对照标准答案 https://27622025.foodvip.net/)
"""
import re, json

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))
tree = data['appendix_a1']['tree']

# 找出 tree 中"坚果及籽类"子树
def find_path(nodes, name, path):
    for n in nodes:
        if n['name'] == name:
            return path + [n['name']]
        if n.get('children'):
            r = find_path(n['children'], name, path + [n['name']])
            if r: return r
    return None

jianguo_path = find_path(tree, '坚果及籽类', [])
print('坚果及籽类 tree path:', ' > '.join(jianguo_path))
print()

# 列出 tree 中坚果及籽类相关的所有节点
print('=== tree 中坚果及籽类相关节点 ===')
for n in tree:
    if '坚果' in n['name']:
        print(f"  {n['name']}")
        for c in n.get('children', []):
            print(f"    {c['name']}")
            for cc in c.get('children', []):
                print(f"      {cc['name']}")

print()

# 标准答案摘要(基于 foodvip):
print('=== 标准答案 (https://27622025.foodvip.net/) ===')
print('L2 坚果及籽类 (catid=97):')
print('  本级 限: 铅 ≤0.2 坚果及籽类(生咖啡豆及烘焙咖啡豆除外)')
print('  上级 L1 锡: ≤250')
print()
print('L3 生干坚果及籽类 (catid=98):')
print('  本级 限: 铅 ≤0.5 生咖啡豆及烘焙咖啡豆')
print('  本级 限: 镉 ≤0.5 花生   <-- 这里花生本应显示!')
print('  上级 L2: 铅 ≤0.2 坚果及籽类(生咖啡豆除外)')
print()
print('L3 坚果及籽类制品 (catid=99):')
print('  本级 无')
print('  上级 L2: 铅 ≤0.2 坚果及籽类(生咖啡豆除外)')
print()
print('L4 熟制坚果及籽类（带壳、脱壳、包衣） (catid=100):')
print('  本级 限: 镉 ≤0.5 花生     <-- 花生在 L4 也应显示')
print('  本级 限: 铅 ≤0.5 生咖啡豆及烘焙咖啡豆')
print('  上级 L2: 铅 ≤0.2')
print()

# 当前 v82-fix26 花生 row 数据
print('=== 当前 v82-fix26 中花生 row 数据 ===')
print('  a1_l1: "坚果及籽类"')
print('  a1_l2/3/4: (空)')
print('  food: "花生"')
print('  → walkExact 注册到 L1 坚果及籽类  (错!)')
print()
print('=== 同时正确的行: 生咖啡豆 ===')
print('  a1_l1: "坚果及籽类"')
print('  a1_l2: "生干坚果及籽类（不包括谷物种子和豆类，包括咖啡豆、可可豆）"')
print('  a1_l3: "生咖啡豆及烘焙咖啡豆"')
print('  → 注册到 L3 生干坚果及籽类 (正确)')