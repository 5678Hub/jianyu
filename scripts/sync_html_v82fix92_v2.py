#!/usr/bin/env python3
"""v82-fix92 HTML 同步 v2：精确插入缺失的 6 个 A.1 节点 + row a1l4"""
import json
import re
import subprocess

with open('jianyu-standalone-v82.html', encoding='utf-8') as f:
    html = f.read()

# 从 git 历史拿节点 catid 信息
r = subprocess.run(['git','show','b0c00ad~1:data/gb2762/gb2762_2025.json'], capture_output=True, text=True, encoding='utf-8')
data_before = json.loads(r.stdout)

def find_node(nodes, name):
    for n in nodes:
        if n.get('name') == name:
            return n
    return None

# 找出 HTML 中每个 L2 节点的 children 数组结尾，插入新节点
# L2 节点结构: { "name": "<L2>", "children": [ ... ] }
# children 数组以 ] 结尾，可能跨多行

# 要添加的 6 个缺失节点
missing_nodes = [
    ('水产动物及其制品', '水产制品', '海蜇制品'),
    ('水产动物及其制品', '水产制品', '鱼类制品'),
    ('水产动物及其制品', '水产制品', '其他鱼类制品'),
    ('水产动物及其制品', '水产制品', '其他水产品'),
    ('其他类（除上述食品以外的食品）', '花粉', '松花粉'),
    ('其他类（除上述食品以外的食品）', '花粉', '油菜花粉'),
]

added = 0
for l1, l2, l4 in missing_nodes:
    # 跳过已存在的
    if f'"name": "{l4}"' in html:
        continue

    # 从 data_before 获取 catid
    n1 = find_node(data_before['appendix_a1']['tree'], l1)
    if not n1: continue
    n2 = find_node(n1.get('children', []), l2)
    if not n2: continue
    n4 = None
    for c in n2.get('children', []):
        if c.get('name') == l4:
            n4 = c
            break
    if not n4: continue

    catid = n4.get('catid', 0)
    if catid:
        node_block = f'''                  {{
                    "catid": {catid},
                    "name": "{l4}",
                    "children": []
                  }},
'''
    else:
        node_block = f'''                  {{
                    "name": "{l4}",
                    "children": []
                  }},
'''

    # 在 HTML 中找 L2 节点的 children 数组结束位置
    # 用查找最后一个出现 "name": "<l2>" 的位置 + 找到对应的 children 数组末尾
    # 简化策略：找 L2 节点后续的 "]" 位置（L2 节点 children 数组的结束）

    # 找 "name": "<l2>",\s*"children": [ 位置
    l2_start = html.find(f'"name": "{l2}"')
    if l2_start == -1:
        print(f'[SKIP] HTML 中找不到 L2: {l2}')
        continue

    # 找 L2 节点对应的 children 数组结束 - 需要找到 L2 块后的第一个外层 "]"
    # 简单方法：在 l2_start 之后找 "children": [，然后数 [] 配对
    bracket_search = html.find('"children": [', l2_start)
    if bracket_search == -1:
        continue

    # 找匹配的 ] - 跳过字符串内容
    pos = bracket_search + len('"children": [')
    depth = 1
    in_string = False
    escape = False
    while pos < len(html) and depth > 0:
        c = html[pos]
        if escape:
            escape = False
        elif c == '\\':
            escape = True
        elif c == '"':
            in_string = not in_string
        elif not in_string:
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    break
        pos += 1

    if depth != 0:
        print(f'[SKIP] {l2} children 数组不平衡')
        continue

    # 在 ] 前插入新节点
    # pos 指向 ]，往前看最后一个字符应该是换行
    # 在 ] 前插入
    insert_pos = pos
    # 在 ] 前加逗号（如果前一个字符不是 , { [ 之类）
    html = html[:insert_pos] + node_block + html[insert_pos:]
    added += 1
    print(f'[OK] HTML 添加 {l1}/{l2}/{l4}')

print(f'\nHTML A.1 节点添加: {added}')

# 3. 恢复 3 条剩余的 row a1l4（之前 v82-fix92 row 5 条已恢复，还有 3 条）
# [砷] 鱼类及其制品 —、 [苯并[a]芘] 熏、烧、烤肉类 5.0、 [N-二甲基亚硝胺] 干制水产品 4.0
# 这些 row 字段不完全匹配，可能 limit_value 为空等

# 用宽松正则：food + pollutant + (任意 limit_value 格式) + a1_l4=""
restore_rows = [
    {'food': '鱼类及其制品', 'pollutant': '砷', 'l4': '鱼类制品'},
    {'food': '熏、烧、烤肉类', 'pollutant': '苯并[a]芘', 'l4': '熏、烧、烤肉类'},
    {'food': '干制水产品', 'pollutant': 'N-二甲基亚硝胺', 'l4': '其他水产品'},
]

restored = 0
for rr in restore_rows:
    # 模式: "food": "<rr.food>",\s*\n\s*"limit" 或 "pollutant": "<rr.pollutant>", ... "a1_l4": ""
    # 砷表用 "limit": "— mg/kg", 苯并芘用 "limit": "5.0 μg/kg"
    pattern = re.compile(
        r'(\{\s*"food":\s*"' + re.escape(rr['food']) +
        r'",\s*\n\s*"[^"]+":\s*"[^"]*",\s*\n(?:[^}]*?)"a1_l4":\s*)""',
        re.DOTALL
    )
    # 更精确：先找包含 food + pollutant 的块，再找 a1l4
    # 用更简单的索引匹配：
    food_pos = html.find(f'"food": "{rr["food"]}"')
    if food_pos == -1:
        print(f'[SKIP] HTML 找不到 food: {rr["food"]}')
        continue
    # 在 food_pos 之后 1500 字符内查找 "a1_l4": ""
    block = html[food_pos:food_pos+2000]
    m = re.search(r'"a1_l4":\s*""', block)
    if m:
        # 替换
        abs_pos = food_pos + m.start()
        html = html[:abs_pos] + f'"a1_l4": "{rr["l4"]}"' + html[abs_pos + len('"a1_l4": ""'):]
        restored += 1
        print(f'[OK] 恢复 [{rr["pollutant"]}] {rr["food"]} → a1l4={rr["l4"]}')
    else:
        print(f'[SKIP] [{rr["pollutant"]}] {rr["food"]} HTML 中找不到空 a1l4')

print(f'\nHTML row a1l4 恢复: {restored}')

with open('jianyu-standalone-v82.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('HTML 已保存')
