"""查 Pb idx=63-72 完整内容"""
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
    if t.get('symbol') == 'Pb':
        for i in range(63, min(73, len(t['items']))):
            it = t['items'][i]
            print(f'[{i}]')
            print(f'  a1_l1={it.get("a1_l1","")[:30]}')
            print(f'  a1_l2={it.get("a1_l2","")[:30]}')
            print(f'  a1_l3={it.get("a1_l3","")[:30]}')
            print(f'  a1_l4="{it.get("a1_l4","")}"')
            print(f'  food={it.get("food","")}')
            print(f'  limit={it.get("limit_value","") or it.get("limit","")} note={it.get("note","")}')
        break