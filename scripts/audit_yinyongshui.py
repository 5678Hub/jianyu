"""扫描「饮料类 > 包装饮用水」L1/L2/L3 row 归属（含 L4 子节点）"""
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
# 找「饮料类」L1 节点
def find_n(nodes, name):
    for n in nodes:
        if n['name'] == name: return n
        if n.get('children'):
            r = find_n(n['children'], name)
            if r: return r
    return None

yinliao = find_n(tree, '饮料类')
print('A.1 树 饮料类节点结构:')
print(f'  {yinliao["name"]}')
for c2 in yinliao.get('children', []):
    print(f'  └─ {c2["name"]}')
    for c3 in c2.get('children', []):
        l4 = c3.get('children', [])
        l4_str = f' (L4: {[x["name"] for x in l4]})' if l4 else ''
        print(f'      └─ {c3["name"]}{l4_str}')

# 扫描所有 row
print('\n\n所有 row（按饮料类子分类）:')
for t in data['contaminants']:
    sym = t.get('symbol', '')
    for idx, it in enumerate(t['items']):
        a1_l1 = it.get('a1_l1', '')
        if a1_l1 != '饮料类':
            continue
        a1_l2 = it.get('a1_l2', '')
        a1_l3 = it.get('a1_l3', '')
        a1_l4 = it.get('a1_l4', '')
        food = it.get('food', '')
        limit = it.get('limit_value', '') or it.get('limit', '') or it.get('main_limit', '')
        sub = it.get('sub_value', '')
        note = it.get('note', '') or it.get('remark', '')
        if not a1_l2:
            lvl = 'L1'
        elif not a1_l3:
            lvl = 'L2'
        elif not a1_l4:
            lvl = 'L3'
        else:
            lvl = 'L4'
        print(f'[{sym:>4}] idx={idx:<3} {lvl} a1l1={a1_l1[:8]} a1l2={a1_l2[:18]:<18} a1l3={a1_l3[:18]:<18} a1l4={a1_l4:<10} food={food[:30]:<30} lim={limit}{("/"+sub) if sub else ""} note={note}')