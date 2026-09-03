"""v82-fix62: 补 Hg '稻谷' L3 own row

用户：「这样我在稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉，都能看到总汞的限量内容才对。」
  → 8 个节点 own 段都显示 1 条 Hg row
  → 当前缺 '稻谷' 1 条

实现：在 idx=12 之后插入 1 条 a1_l3='稻谷' 的复制 row
"""
import re, json, copy

SRC = r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'<script type="application/json" id="inlineData">', content)
start = m.end()
depth = 0; in_str = False; esc = False; i = start
while i < len(content):
    ch = content[i]
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
    else:
        if ch == '"': in_str = True
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: end = i + 1; break
    i += 1
data = json.loads(content[start:end])

hg = None
for t in data['contaminants']:
    if t.get('symbol') == 'Hg':
        hg = t; break
assert hg, 'Hg table not found'

items = hg['items']
print(f'Hg items count before: {len(items)}')

# idx=13 当前是 '玉米'，idx=14-19 是其他 6 个 L3/L4 节点
# 找 idx=12 之后第一个非 '稻谷' 节点 row（即 idx=13='玉米'），在 idx=12 之后插入 '稻谷'
template = items[12]
new_row = copy.deepcopy(template)
new_row['a1_l2'] = '谷物'
new_row['a1_l3'] = '稻谷'
new_row['a1_l4'] = ''
print(f'[INSERT] a1_l2={new_row["a1_l2"]} a1_l3={new_row["a1_l3"]} a1_l4="{new_row["a1_l4"]}"')

# 插在 position 13（idx=12 之后）
items.insert(13, new_row)
print(f'Hg items count after: {len(items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix61[^"]*"',
    '"_last_fix": "v82-fix62-add-hg-daogu-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix61\][^<]*',
    '[v82-fix62] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix62 applied')