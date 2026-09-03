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

# 检查 additives 结构
print('additives 数量:', len(data['additives']))
ad = data['additives'][2]
print('additives[2] keys:', list(ad.keys()))
print('additives[2] name:', ad.get('name'))
print('additives[2] rows 数量:', len(ad['rows']))
print('第一行 sample:', json.dumps(ad['rows'][0], ensure_ascii=False)[:300])

# 统计 additives 中 sub/path 含 wrong 的
cnt = 0
examples = []
for ai, a in enumerate(data['additives']):
    for ri, row in enumerate(a.get('rows', [])):
        sub = row.get('sub', '')
        path = row.get('path', '')
        if sub in wrong or any(w in path for w in wrong):
            cnt += 1
            if len(examples) < 5:
                examples.append((ai, ri, sub, path))
print(f'\nadditives 中含错误 sub/path 的条目: {cnt}')
for e in examples:
    print(f'  additives[{e[0]}].rows[{e[1]}] sub={e[2]} path={e[3]}')

# 也检查 appendix_a1 是否含这些信息
print('\nappendix_a1 type:', type(data.get('appendix_a1')).__name__)
if isinstance(data.get('appendix_a1'), dict):
    print('  keys:', list(data['appendix_a1'].keys())[:10])
