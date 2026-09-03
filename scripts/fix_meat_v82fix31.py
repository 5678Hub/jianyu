import re, json

path = 'jianyu-standalone-v82.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# ===== 1. 删除 4 个假节点 =====
# 肉类(105) 下 畜禽肝脏, 畜禽肾脏 (是 catid=107 的兄弟, 在 catid=105 children 里)
old105_1 = '{"catid":105,"name":"肉类（生鲜肉、冷却肉、冷冻肉等）","children":[{"catid":106,"name":"畜禽肉","children":[]},{"catid":107,"name":"畜禽内脏（例如：肝、肾、肺、肠等）","children":[]},{"name":"畜禽肝脏","children":[]},{"name":"畜禽肾脏","children":[]}]}'
new105_1 = '{"catid":105,"name":"肉类（生鲜肉、冷却肉、冷冻肉等）","children":[{"catid":106,"name":"畜禽肉","children":[]},{"catid":107,"name":"畜禽内脏（例如：肝、肾、肺、肠等）","children":[]}]}'
assert html.count(old105_1) == 1, f'old105_1 count={html.count(old105_1)}'
html = html.replace(old105_1, new105_1)
print('[1] 肉类(catid=105): 删除 畜禽肝脏, 畜禽肾脏 ✓')

# 肉制品(108) 下 畜禽内脏制品, 熏、烧、烤肉类 (在 catid=112 关闭之后, catid=108 children 尾)
# 只删除两个 fake 节点本身 (含前导逗号), 保留 catid=108 的关闭 ]}
old108_1 = ',{"name":"畜禽内脏制品","children":[]},{"name":"熏、烧、烤肉类","children":[]}'
new108_1 = ''
assert html.count(old108_1) == 1, f'old108_1 count={html.count(old108_1)}'
html = html.replace(old108_1, new108_1)
print('[2] 肉制品(catid=108): 删除 畜禽内脏制品, 熏、烧、烤肉类 ✓')

# ===== 2. 解析 inlineData =====
m = re.search(r'<script type="application/json" id="inlineData">', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg = html[seg_start:seg_start+m2.start()]

depth = 0; obj_end = -1; in_str = False; esc = False
for i, ch in enumerate(seg):
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
        continue
    if ch == '"': in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = i+1; break

data = json.loads(seg[:obj_end])

# ===== 3. 修正 contaminants rows =====
fixed_cont = 0
for cont in data['contaminants']:
    for it in cont['items']:
        l4 = it.get('a1_l4','')
        if l4 == '畜禽肝脏' or l4 == '畜禽肾脏':
            it['a1_l3'] = '畜禽内脏（例如：肝、肾、肺、肠等）'
            it['a1_l4'] = ''
            fixed_cont += 1
        elif l4 == '畜禽内脏制品':
            it['a1_l4'] = ''
            fixed_cont += 1
        elif l4 == '熏、烧、烤肉类':
            it['a1_l3'] = '熟肉制品'
            it['a1_l4'] = '熏、烧、烤肉类'
            fixed_cont += 1

print(f'[3] contaminants 修正 {fixed_cont} 行 a1_l ✓')

# ===== 4. 修正 additives rows =====
fixed_add = 0
for a in data['additives']:
    for row in a.get('rows', []):
        row_path = row.get('path','')
        if row_path.endswith(':畜禽肝脏') or ':畜禽肝脏,' in row_path:
            row['parts'] = ['肉及肉制品', '肉类（生鲜肉、冷却肉、冷冻肉等）', '畜禽内脏（例如：肝、肾、肺、肠等）']
            row['path'] = '肉及肉制品:肉类（生鲜肉、冷却肉、冷冻肉等）:畜禽内脏（例如：肝、肾、肺、肠等）'
            row['sub'] = '畜禽内脏（例如：肝、肾、肺、肠等）'
            fixed_add += 1
        elif row_path.endswith(':畜禽肾脏') or ':畜禽肾脏,' in row_path:
            row['parts'] = ['肉及肉制品', '肉类（生鲜肉、冷却肉、冷冻肉等）', '畜禽内脏（例如：肝、肾、肺、肠等）']
            row['path'] = '肉及肉制品:肉类（生鲜肉、冷却肉、冷冻肉等）:畜禽内脏（例如：肝、肾、肺、肠等）'
            row['sub'] = '畜禽内脏（例如：肝、肾、肺、肠等）'
            fixed_add += 1
        elif ':畜禽内脏制品' in row_path:
            row['parts'] = ['肉及肉制品', '肉制品（包括内脏制品、血制品）']
            row['path'] = '肉及肉制品:肉制品（包括内脏制品、血制品）'
            row['sub'] = '肉制品（包括内脏制品、血制品）'
            fixed_add += 1
        elif row_path.endswith('肉及肉制品:熏、烧、烤肉类'):
            row['parts'] = ['肉及肉制品', '肉制品（包括内脏制品、血制品）', '熟肉制品', '熏、烧、烤肉类']
            row['path'] = '肉及肉制品:肉制品（包括内脏制品、血制品）:熟肉制品:熏、烧、烤肉类'
            row['sub'] = '熏、烧、烤肉类'
            fixed_add += 1

print(f'[4] additives 修正 {fixed_add} 行 sub/path/parts ✓')

# ===== 5. 回写 =====
new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start+m2.start():]
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
print('[5] 写入完成')