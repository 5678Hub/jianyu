"""v82-fix73: 删 Cd idx=3-8 冗余 row + 复制 idx=2 到「糙米」「大米(粉)」L3

PDF Cd 列谷物只有 3 行：
- 谷物〔稻谷除外〕0.1（L2 通类）
- 谷物碾磨加工品〔糙米、大米（粉）除外〕0.1（L2 通类）
- 稻谷a、糙米、大米(粉)0.2（合并入口）

idx=3-8 是历史数据冗余（PDF 无原 row），应删。
idx=2 复制 2 份到「糙米」「大米(粉)」L3，保证 own 段显示 Cd 0.2。

修复后 Cd 谷物 5 条 row：
- idx=0 L2「谷物〔稻谷除外〕」
- idx=1 L2「谷物碾磨加工品〔糙米、大米（粉）除外〕」
- idx=2 L3「稻谷」合并入口
- idx=3 L3「糙米」复制（v82-fix73 新加）
- idx=4 L3「大米(粉)」复制（v82-fix73 新加）
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

cd = None
for t in data['contaminants']:
    if t.get('symbol') == 'Cd':
        cd = t; break
assert cd

cd_items = cd['items']
print(f'Cd items count before: {len(cd_items)}')

# 1) 删 idx=3-8 (6 条冗余 row)
to_delete = [3, 4, 5, 6, 7, 8]
print(f'[DELETE] positions {to_delete}')
for idx in sorted(to_delete, reverse=True):
    del cd_items[idx]
    print(f'  deleted pos={idx}')

# 2) 复制 idx=2 到「糙米」「大米(粉)」L3
# idx=2 当前是「稻谷」L3 合并入口
template = cd_items[2]
print(f'[TEMPLATE idx=2] a1_l3={template["a1_l3"]} food={template["food"]}')

mounts = [
    {'a1_l2': '谷物碾磨加工品', 'a1_l3': '糙米（包括色稻米）', 'a1_l4': ''},
    {'a1_l2': '谷物碾磨加工品', 'a1_l3': '大米（粉）',         'a1_l4': ''},
]
new_rows = []
for m_def in mounts:
    new_row = copy.deepcopy(template)
    new_row['a1_l2'] = m_def['a1_l2']
    new_row['a1_l3'] = m_def['a1_l3']
    new_row['a1_l4'] = m_def['a1_l4']
    new_rows.append(new_row)
    print(f'[INSERT Cd] a1_l2={m_def["a1_l2"]} a1_l3={m_def["a1_l3"]}')

# 插在 position 3（idx=2 后）
cd_items[3:3] = new_rows
print(f'Cd items count after: {len(cd_items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix72[^"]*"',
    '"_last_fix": "v82-fix73-clean-cd-grain-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix72\][^<]*',
    '[v82-fix73] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('\nOK: v82-fix73 applied')