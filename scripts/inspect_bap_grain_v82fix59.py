"""查看 BaP 在谷物下的全部 rows"""
import re, json

with open(r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'<script type="application/json" id="inlineData">', content)
start = m.end()
depth = 0
i = start
in_string = False
escape = False
while i < len(content):
    c = content[i]
    if in_string:
        if escape:
            escape = False
        elif c == '\\':
            escape = True
        elif c == '"':
            in_string = False
    else:
        if c == '"':
            in_string = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    i += 1

data = json.loads(content[start:end])
items = data['items']

print('=== BaP rows in 谷物及其制品 ===')
for it in items:
    p = str(it.get('pollutant', ''))
    if '苯并' in p or p == 'BaP':
        cat = it.get('category_path', '')
        if '谷物' in cat:
            print(f"idx={it.get('idx')} cat='{cat}'")
            print(f"  food='{it.get('food','')}'")
            print(f"  limit='{it.get('limit','')}' note='{it.get('note','')}'")
            print()

print(f'Total items: {len(items)}')