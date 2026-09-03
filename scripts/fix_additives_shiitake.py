import re, json

path = 'jianyu-standalone-v82.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()
m = re.search(r'<script type="application/json" id="inlineData">', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg = html[seg_start:seg_start+m2.start()]

depth = 0
obj_end = -1
in_str = False
esc = False
for i, ch in enumerate(seg):
    if in_str:
        if esc:
            esc = False
        elif ch == '\\':
            esc = True
        elif ch == '"':
            in_str = False
        continue
    if ch == '"':
        in_str = True
    elif ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            obj_end = i + 1
            break

data = json.loads(seg[:obj_end])

wrong = {'松茸制品','松露制品','牛肝菌制品','鸡枞制品','多汁乳菇制品','羊肚菌制品','獐头菌制品','青头菌制品','鸡油菌制品','榛蘑制品','姬松茸制品','香菇制品','木耳制品','银耳制品'}

fixed = 0
for a in data['additives']:
    for row in a.get('rows', []):
        p = row.get('path', '')
        if any(w in p for w in wrong):
            row['sub'] = '其他食用菌制品'
            row['parts'] = ['食用菌及其制品', '食用菌制品', '其他食用菌制品']
            row['path'] = '食用菌及其制品:食用菌制品:其他食用菌制品'
            fixed += 1

print(f'additives 修正 {fixed} 行 sub/path/parts -> 其他食用菌制品')

new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start+m2.start():]
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print('FILE WRITTEN')
