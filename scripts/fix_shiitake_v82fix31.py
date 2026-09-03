import re, json

path = 'jianyu-standalone-v82.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# ===== 1. 删除 catid=50 下 14 个错误节点 =====
old_block = '{"catid":50,"name":"食用菌制品","children":[{"catid":51,"name":"食用菌罐头","children":[]},{"catid":52,"name":"腌渍食用菌（例如：酱渍、盐渍、糖醋渍食用菌等）","children":[]},{"catid":53,"name":"经水煮或油炸的食用菌","children":[]},{"catid":54,"name":"其他食用菌制品","children":[]},{"name":"松茸制品","children":[]},{"name":"松露制品","children":[]},{"name":"牛肝菌制品","children":[]},{"name":"鸡枞制品","children":[]},{"name":"多汁乳菇制品","children":[]},{"name":"羊肚菌制品","children":[]},{"name":"獐头菌制品","children":[]},{"name":"青头菌制品","children":[]},{"name":"鸡油菌制品","children":[]},{"name":"榛蘑制品","children":[]},{"name":"姬松茸制品","children":[]},{"name":"香菇制品","children":[]},{"name":"木耳制品","children":[]},{"name":"银耳制品","children":[]}]}'
new_block = '{"catid":50,"name":"食用菌制品","children":[{"catid":51,"name":"食用菌罐头","children":[]},{"catid":52,"name":"腌渍食用菌（例如：酱渍、盐渍、糖醋渍食用菌等）","children":[]},{"catid":53,"name":"经水煮或油炸的食用菌","children":[]},{"catid":54,"name":"其他食用菌制品","children":[]}]}'
assert html.count(old_block) == 1, 'old_block not found exactly once'
html = html.replace(old_block, new_block)
print('[1] tree: removed 14 wrong nodes under catid=50 OK')

# ===== 2. 解析 inlineData 第一个平衡对象 =====
m = re.search(r'<script type="application/json" id="inlineData">', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg_end = seg_start + m2.start()
seg = html[seg_start:seg_end]

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
print('[2] first JSON object ends at', obj_end, '; trailing len', len(seg) - obj_end)

data = json.loads(seg[:obj_end])
print('    top keys:', list(data.keys()))

wrong_l4 = {'松茸制品','松露制品','牛肝菌制品','鸡枞制品','多汁乳菇制品','羊肚菌制品','獐头菌制品','青头菌制品','鸡油菌制品','榛蘑制品','姬松茸制品','香菇制品','木耳制品','银耳制品'}

fixed = 0
for cont in data['contaminants']:
    for it in cont['items']:
        if it.get('a1_l4', '') in wrong_l4:
            it['a1_l4'] = ''
            if it.get('a1_l2', '') == '食用菌制品':
                it['a1_l3'] = '其他食用菌制品'
            fixed += 1

before = sum(len(c['items']) for c in data['contaminants'])
for cont in data['contaminants']:
    seen = set()
    new_items = []
    for it in cont['items']:
        key = (it.get('food'), it.get('limit_value'), it.get('a1_l1'), it.get('a1_l2'), it.get('a1_l3'), it.get('a1_l4'), it.get('has_limit'))
        if key not in seen:
            seen.add(key)
            new_items.append(it)
    cont['items'] = new_items
after = sum(len(c['items']) for c in data['contaminants'])
print(f'[3] fixed {fixed} rows a1_l4 -> 其他食用菌制品 OK')
print(f'[4] dedup: {before} -> {after} rows (removed {before-after})')

new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_end:]
print('[5] inlineData written back OK')

with open(path, 'w', encoding='utf-8') as f:
    html = f.write(html)
print('FILE WRITTEN')
