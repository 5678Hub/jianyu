"""列出所有 L1 own rows（a1_l1 != '' 且 a1_l2 == ''），供 v82-fix66 审计"""
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

for t in data['contaminants']:
    sym = t.get('symbol') or t.get('contaminant','')
    items = t['items']
    for i, it in enumerate(items):
        a1 = it.get('a1_l1','').strip()
        a2 = it.get('a1_l2','').strip()
        a3 = it.get('a1_l3','').strip()
        a4 = it.get('a1_l4','').strip()
        if a1 and not a2 and not a3 and not a4:
            #  L1 own row（a1_l1 only）
            food = it.get('food','')
            lv = it.get('limit_value') or it.get('limit','')
            print(f'[{sym} idx={i}] food={food[:60]} limit={lv}')