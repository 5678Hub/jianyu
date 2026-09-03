"""扫描所有污染物 → 谷物及其制品 L1/L2/L3/L4 行归属审计"""
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

# 谷物及其制品（不包括焙烤制品）相关的所有污染物行
L1 = '谷物及其制品（不包括焙烤制品）'
print('=' * 100)
print('L1：谷物及其制品（不包括焙烤制品）')
print('=' * 100)
for t in data['contaminants']:
    sym = t.get('symbol', '')
    for idx, it in enumerate(t['items']):
        a1_l1 = it.get('a1_l1', '')
        if a1_l1 != L1:
            continue
        a1_l2 = it.get('a1_l2', '')
        a1_l3 = it.get('a1_l3', '')
        a1_l4 = it.get('a1_l4', '')
        food = it.get('food', '')
        limit = it.get('limit_value', '') or it.get('limit', '') or it.get('main_limit', '')
        sub = it.get('sub_value', '')
        note = it.get('note', '') or it.get('remark', '')
        # 决定层级
        if not a1_l2:
            lvl = 'L1'
        elif not a1_l3:
            lvl = 'L2'
        elif not a1_l4:
            lvl = 'L3'
        else:
            lvl = 'L4'
        print(f'[{sym:>4}] idx={idx:<3} {lvl} a1l1={a1_l1[:18]:<18} a1l2={a1_l2[:18]:<18} a1l3={a1_l3[:18]:<18} a1l4={a1_l4:<10} food={food[:30]:<30} lim={limit}{("/"+sub) if sub else ""} note={note}')