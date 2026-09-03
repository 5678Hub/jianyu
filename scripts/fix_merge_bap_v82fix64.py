"""v82-fix64: 合并 BaP idx=8+idx=9 为「玉米粉、玉米糁(渣)」+ 清空 idx=7/idx=10 a1_l4

用户：「合并成为一个，玉米粉、玉米糁（渣）。这两条，本来也是一个 food 名称。不应该拆开的」
  → idx=8 (a1_l4='玉米粉' food='玉米粉') 和 idx=9 (a1_l4='玉米糁(渣)' food='玉米糁(渣)')
  → A.1 树 L3 '玉米粉、玉米糁（渣）' 没 L4 子节点，Fallback B 让两者都 fall back 到同一 L3 → 重复显示

修复：
- idx=8 food='玉米粉、玉米糁(渣)' a1_l4=''
- 删 idx=9
- idx=7 a1_l4=''（与 v82-fix63 Hg 同步，A.1 '小麦粉（包括食用麸皮）' L3 没 L4）
- idx=10 a1_l4=''（同上，'糙米（包括色稻米）' L3 没 L4）
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

bap = None
for t in data['contaminants']:
    if t.get('symbol') == 'BaP':
        bap = t; break
assert bap, 'BaP table not found'

items = bap['items']
print(f'BaP items count before: {len(items)}')

# 1) idx=8 food='玉米粉、玉米糁(渣)' a1_l4=''
items[8]['food'] = '玉米粉、玉米糁(渣)'
items[8]['a1_l4'] = ''
print(f'[MERGE] idx=8 food=玉米粉、玉米糁(渣) a1_l4=""')

# 2) 删 idx=9（idx=8 后面的「玉米糁(渣)」重复 row）
del items[9]
print(f'[DELETE] idx=9 (玉米糁(渣) 重复 row)')

# 3) idx=7 a1_l4=''（v82-fix63 同步：清空无意义 L4 字段，A.1 '小麦粉（包括食用麸皮）' L3 没 L4）
items[7]['a1_l4'] = ''
print(f'[CLEANUP] idx=7 a1_l4=""')

# 4) 原 idx=10（糙米 a1_l4='糙米'）删 idx=9 后变成 idx=9，a1_l4 清空
items[9]['a1_l4'] = ''
print(f'[CLEANUP] idx=9（原 idx=10 糙米）a1_l4=""')

print(f'BaP items count after: {len(items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix63[^"]*"',
    '"_last_fix": "v82-fix64-merge-bap-yumi-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix63\][^<]*',
    '[v82-fix64] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix64 applied')