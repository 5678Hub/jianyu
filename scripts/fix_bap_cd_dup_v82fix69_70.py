"""v82-fix69 + v82-fix70: 一次性合并执行

v82-fix69: BaP idx=5 复制 7 份到 7 个 L3 节点 + 删 idx=4「小麦」
  8 个 L3 节点：稻谷(idx=5自身) + 玉米/小麦/糙米/大米/小麦粉/玉米粉、玉米糁(渣)

v82-fix70: Cd idx=2 复制 2 份到「糙米」「大米(粉)」L3 节点
  3 个 L3 节点：稻谷(idx=2自身) + 糙米/大米(粉)
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

# ====== v82-fix69: BaP idx=5 复制 + 删 idx=4 =======
bap = None
for t in data['contaminants']:
    if t.get('symbol') == 'BaP':
        bap = t; break
assert bap

bap_items = bap['items']
print(f'BaP items count before: {len(bap_items)}')

# idx=4 当前是「小麦」简略 row (a1_l2='谷物' a1_l3='小麦')
idx4_target = bap_items[4]
print(f'[TARGET DEL idx=4] a1_l3={idx4_target["a1_l3"]} food={idx4_target["food"]}')

# idx=5 当前是「稻谷」合并表达 row
idx5_template = bap_items[5]
print(f'[TEMPLATE idx=5] a1_l3={idx5_template["a1_l3"]} food={idx5_template["food"][:30]}...')

# 1) 删 idx=4
del bap_items[4]
print(f'[DELETE] idx=4 (小麦 简略 row)')

# 2) 在 idx=5 后（现 position 5）插入 7 份复制到 7 个 L3 节点
mounts_bap = [
    {'a1_l2': '谷物',                'a1_l3': '玉米',                  'a1_l4': ''},          # 玉米
    {'a1_l2': '谷物',                'a1_l3': '小麦',                  'a1_l4': ''},          # 小麦
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '糙米（包括色稻米）',     'a1_l4': ''},          # 糙米
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '大米（粉）',            'a1_l4': ''},          # 大米
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '小麦粉（包括食用麸皮）', 'a1_l4': ''},          # 小麦粉
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '玉米粉、玉米糁（渣）',   'a1_l4': ''},          # 玉米粉、玉米糁(渣)
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '稻谷',                  'a1_l4': ''},          # 稻谷（idx=5自身已挂，再加一份复制，保持 8 个 L3 节点对称）
]
new_bap_rows = []
for m_def in mounts_bap:
    new_row = copy.deepcopy(idx5_template)
    new_row['a1_l2'] = m_def['a1_l2']
    new_row['a1_l3'] = m_def['a1_l3']
    new_row['a1_l4'] = m_def['a1_l4']
    new_bap_rows.append(new_row)
    print(f'[INSERT BaP] a1_l2={m_def["a1_l2"]} a1_l3={m_def["a1_l3"]}')

# 插在 position 5（idx=5 后）
bap_items[5:5] = new_bap_rows
print(f'BaP items count after: {len(bap_items)}')

# ====== v82-fix70: Cd idx=2 复制 2 份 =======
cd = None
for t in data['contaminants']:
    if t.get('symbol') == 'Cd':
        cd = t; break
assert cd

cd_items = cd['items']
print(f'\nCd items count before: {len(cd_items)}')

idx2_template = cd_items[2]
print(f'[TEMPLATE idx=2] a1_l2={idx2_template["a1_l2"]} a1_l3={idx2_template["a1_l3"]} food={idx2_template["food"]}')

mounts_cd = [
    {'a1_l2': '谷物碾磨加工品', 'a1_l3': '糙米（包括色稻米）', 'a1_l4': ''},
    {'a1_l2': '谷物碾磨加工品', 'a1_l3': '大米（粉）',         'a1_l4': ''},
]
new_cd_rows = []
for m_def in mounts_cd:
    new_row = copy.deepcopy(idx2_template)
    new_row['a1_l2'] = m_def['a1_l2']
    new_row['a1_l3'] = m_def['a1_l3']
    new_row['a1_l4'] = m_def['a1_l4']
    new_cd_rows.append(new_row)
    print(f'[INSERT Cd] a1_l2={m_def["a1_l2"]} a1_l3={m_def["a1_l3"]}')

cd_items[3:3] = new_cd_rows
print(f'Cd items count after: {len(cd_items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix68[^"]*"',
    '"_last_fix": "v82-fix69-70-bap-cd-dup-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix68\][^<]*',
    '[v82-fix69-70] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('\nOK: v82-fix69-70 applied')