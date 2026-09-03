#!/usr/bin/env python3
"""v82-fix92 HTML 同步：恢复 7 个 A.1 节点 + 8 条 row a1l4"""
import json
import subprocess

with open('jianyu-standalone-v82.html', encoding='utf-8') as f:
    html = f.read()

# 1. 恢复 A.1 树节点定义块
# 7 个节点（HTML 中以块状 {"name": "X", "children": [], "catid": Y} 形式存在）
restore_nodes = [
    ('肉及肉制品', '肉制品（包括内脏制品、血制品）', '熏、烧、烤肉类', 115),  # catid 来自之前备份
    ('水产动物及其制品', '水产制品', '海蜇制品', None),
    ('水产动物及其制品', '水产制品', '鱼类制品', None),
    ('水产动物及其制品', '水产制品', '其他鱼类制品', None),
    ('水产动物及其制品', '水产制品', '其他水产品', None),
    ('其他类（除上述食品以外的食品）', '花粉', '松花粉', None),
    ('其他类（除上述食品以外的食品）', '花粉', '油菜花粉', None),
]

# 从 git 历史恢复节点定义
r = subprocess.run(['git','show','b0c00ad~1:data/gb2762/gb2762_2025.json'], capture_output=True, text=True, encoding='utf-8')
data_before = json.loads(r.stdout)

def find_node(nodes, name):
    for n in nodes:
        if n.get('name') == name:
            return n
    return None

import re

added_html = 0
for l1, l2, l4, catid_hint in restore_nodes:
    # 在 data_before 中找完整节点定义
    n1 = find_node(data_before['appendix_a1']['tree'], l1)
    if not n1: continue
    n2 = find_node(n1.get('children', []), l2)
    if not n2: continue
    n4_old = None
    for c in n2.get('children', []):
        if c.get('name') == l4:
            n4_old = c
            break
    if not n4_old: continue

    # 序列化节点
    # HTML 中节点格式: {"name": "...", "catid": N, "children": []}
    catid = n4_old.get('catid', catid_hint or 0)
    if catid:
        node_block = f'''                {{
                    "catid": {catid},
                    "name": "{l4}",
                    "children": []
                  }},
'''
    else:
        node_block = f'''                {{
                    "name": "{l4}",
                    "children": []
                  }},
'''

    # 在 HTML 中找 l2 节点的 children 数组结尾并插入
    # 模式: "name": "<l2>",\s*"children":\s*\[\s*\n(.*?)\n\s*\]
    l2_pattern = re.compile(
        r'\{\s*"name":\s*"' + re.escape(l2) + r'",\s*"children":\s*\[\s*\n(.*?)\n\s*\]\s*\}',
        re.DOTALL
    )
    m = l2_pattern.search(html)
    if not m:
        print(f'[SKIP HTML] 找不到 {l2} 块')
        continue

    # 在 children 数组结尾前插入
    # 找到最后一个 "}," 后面
    children_content = m.group(1)
    # 在 children_content 末尾前插入新节点
    new_children = children_content.rstrip() + '\n' + node_block.rstrip() + '\n'
    html = html[:m.start(1)] + new_children + html[m.end(1):]
    added_html += 1
    print(f'[HTML OK] 恢复 {l1}/{l2}/{l4}')

print(f'\nHTML A.1 树恢复: {added_html} 个节点')

# 2. 恢复 8 条 row 的 a1l4 字段
# row 在 HTML 内嵌数据中，找 "a1_l4": "" 的行，根据上下文 food/pol 还原
# 我们用 git 历史中备份的 row 定义来定位

# 收集 8 条 row 的关键信息
restore_rows = []
for c in data_before['contaminants']:
    name = c.get('contaminant','')
    for item in c.get('items',[]):
        l4 = item.get('a1_l4','')
        if l4 and l4 in ['熏、烧、烤肉类','海蜇制品','鱼类制品','其他鱼类制品','其他水产品','松花粉','油菜花粉']:
            restore_rows.append({
                'food': item.get('food',''),
                'pollutant': name,
                'limit_value': item.get('limit_value','') or item.get('limit',''),
                'l4': l4,
            })

restored = 0
for rr in restore_rows:
    # 在 HTML 中找匹配 food + pollutant + limit_value + a1l4="" 的 row
    # 构造正则
    pattern = re.compile(
        r'\{\s*"food":\s*"' + re.escape(rr['food']) +
        r'",\s*\n\s*(?:"pollutant"|"limit"):\s*"' + re.escape(rr['pollutant']) +
        r'",\s*\n\s*"limit_value":\s*"' + re.escape(rr['limit_value']) +
        r'",\s*\n(?:.*?)"a1_l4":\s*""',
        re.DOTALL
    )
    new_html, count = pattern.subn(
        lambda m: m.group(0).replace('"a1_l4": ""', f'"a1_l4": "{rr["l4"]}"'),
        html, count=1
    )
    if count > 0:
        html = new_html
        restored += 1
        print(f'[HTML OK] 恢复 row [{rr["pollutant"]}] {rr["food"]} → a1l4={rr["l4"]}')
    else:
        print(f'[SKIP] 找不到 [{rr["pollutant"]}] {rr["food"]} {rr["limit_value"]}')

print(f'\nHTML row a1l4 恢复: {restored} 条')

# 写回
with open('jianyu-standalone-v82.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('HTML 同步完成')
