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

# 递归找含 香菇制品 的条目, 打印其祖先 key 路径
hits = []
def walk(o, keypath):
    if isinstance(o, dict):
        s = json.dumps(o, ensure_ascii=False)
        if '香菇制品' in s:
            # 只报告叶子级含 sub/path 的
            if 'path' in o or 'sub' in o:
                hits.append((keypath, o))
        for k, v in o.items():
            walk(v, keypath + [k])
    elif isinstance(o, list):
        for idx, v in enumerate(o):
            walk(v, keypath + [f'[{idx}]'])

walk(data, [])
print('含 香菇制品 的 path/sub 条目数:', len(hits))
for kp, o in hits[:8]:
    print('  keypath:', '.'.join(str(x) for x in kp[:6]), '...')
    print('    ', {kk: o[kk] for kk in ('path','parts','big','sub','food') if kk in o})
