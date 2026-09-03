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

# 找所有引用 畜禽肝脏/畜禽肾脏/畜禽内脏制品/熏、烧、烤肉类 的 row
targets = {'畜禽肝脏','畜禽肾脏','畜禽内脏制品','熏、烧、烤肉类'}
print('=== 引用假节点的污染物 row (修改前) ===')
rows = []
for cont in data['contaminants']:
    for it in cont['items']:
        for k in ['a1_l1','a1_l2','a1_l3','a1_l4']:
            if it.get(k,'') in targets:
                rows.append((cont['contaminant'], it))
                break
for c, it in rows:
    print(f"  {c:>6} | {it['food'][:35]:<35} | a1_l1={it.get('a1_l1','')}")
    print(f"         a1_l2={it.get('a1_l2','')}")
    print(f"         a1_l3={it.get('a1_l3','')}")
    print(f"         a1_l4={it.get('a1_l4','')}")
    print()

# 也找 additives
print('=== additives 中引用假节点 ===')
for ai, a in enumerate(data['additives']):
    for ri, row in enumerate(a.get('rows', [])):
        if any(t in row.get('path','') for t in targets):
            print(f"  additives[{ai}].rows[{ri}]: path={row.get('path')} sub={row.get('sub')} food={row.get('food')}")
