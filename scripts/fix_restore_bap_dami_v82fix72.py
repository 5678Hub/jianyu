"""v82-fix72: 修复 v82-fix71 误删

v82-fix71 错删 idx=6「大米(粉)」简略版（位置 12 是 idx=6，不是「稻谷」复制）
v82-fix71 漏删 mounts_bap[2]「糙米」复制（position 7，导致「糙米」L3 仍有重复）

修复：
- 恢复 idx=6「大米(粉)」简略版：在 position 11 后插入
- 删 position 7「糙米」复制（mounts_bap[2]）
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
assert bap
print(f'BaP items count before: {len(bap["items"])}')

# 当前状态（v82-fix71 后）：
# position 0-7: idx=0-3 + idx=5 入口（稻谷）+ mounts_bap[0-2]（玉米/小麦/糙米）
# position 8: 原 idx=9「糙米」简略
# position 9: 原 idx=10/idx=7「小麦粉」简略
# position 10: 原 idx=11/idx=8「玉米粉、玉米糁(渣)」简略

# 缺失：idx=6「大米(粉)」简略（v82-fix71 错删）

# 1) 找 idx=7「小麦粉」简略作为模板
template_idx = None
for i, it in enumerate(bap['items']):
    if it.get('a1_l3') == '大米（粉）' and it.get('food') == '大米(粉)':
        template_idx = i
        print(f'[TEMPLATE] position {i}: a1_l3={it["a1_l3"]} food={it["food"]}')
        break

assert template_idx is None, '大米(粉) 简略已存在？不需要修复'

# 模板用 idx=8「小麦粉」简略
template_idx = 8  # idx=8 当前是「小麦粉」简略
template = bap['items'][template_idx]
new_row = copy.deepcopy(template)
new_row['a1_l3'] = '大米（粉）'
new_row['a1_l4'] = ''
new_row['food'] = '大米(粉)'

# 插入到 position 9 后（即 position 9 之前，与 idx=8「小麦粉」相邻）
bap['items'].insert(9, new_row)
print(f'[INSERT] position 9: a1_l3=大米（粉） food=大米(粉)')

# 2) 删 position 7「糙米」复制（mounts_bap[2]）
daogu_idx = 7
print(f'[DELETE] position {daogu_idx}: {bap["items"][daogu_idx]["a1_l3"]} 复制')
del bap['items'][daogu_idx]

print(f'BaP items count after: {len(bap["items"])}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix71[^"]*"',
    '"_last_fix": "v82-fix72-fix-v71-wrongdelete-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix71\][^<]*',
    '[v82-fix72] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('\nOK: v82-fix72 applied')