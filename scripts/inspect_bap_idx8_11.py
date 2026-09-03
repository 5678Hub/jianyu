"""检查 BaP idx=8/9/10/11 当前内容"""
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
    if t.get('symbol') == 'BaP':
        print(f'TABLE: symbol={t.get("symbol")}')
        for i in [4, 5, 6, 7, 8, 9, 10, 11]:
            it = t['items'][i]
            print(f'[{i}] keys={list(it.keys())}')
            print(f'    a1_l1={it.get("a1_l1","")[:30]} a1_l2={it.get("a1_l2","")[:30]} a1_l3={it.get("a1_l3","")[:30]} a1_l4={it.get("a1_l4","")[:30]}')
            print(f'    food={it.get("food","")} limit={it.get("limit_value","")}')
        break