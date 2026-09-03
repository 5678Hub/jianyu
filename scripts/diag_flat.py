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
print('top keys:', list(data.keys()))
for k, v in data.items():
    if isinstance(v, list) and v and isinstance(v[0], dict):
        sample = v[0]
        has_sub = 'sub' in sample
        cnt = sum(1 for x in v if isinstance(x, dict) and '香菇制品' in str(x.get('sub', '')) + str(x.get('path', '')))
        print(f'  {k}: len={len(v)} keys={list(sample.keys())} 含香菇制品={cnt}')
