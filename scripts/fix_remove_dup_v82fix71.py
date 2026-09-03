"""v82-fix71: 删 v82-fix69/70 错加的复制（保留各自简略版）

策略修正：
- Cd：删 v82-fix70 新增的 idx=2 复制到「糙米」「大米(粉)」L3（保留 idx=3/4 各自简略）
- BaP：删 v82-fix69 错加的 5 条复制（保留 idx=6/7/8/9 各自简略 + idx=5「稻谷」入口 + idx=6「玉米」idx=7「小麦」复制）

最终结构：
- 「稻谷」own 段：Cd idx=2（合并入口）+ BaP idx=5（合并入口）
- 「玉米」own 段：Hg idx=13 + BaP idx=6（合并复制）
- 「小麦」own 段：Hg idx=14 + BaP idx=7（合并复制）
- 「糙米」own 段：Pb idx=64 + Cd idx=3 简略 + Hg idx=15 + As idx=25 + BaP idx=9 简略
- 「大米(粉)」own 段：Cd idx=4 简略 + Hg idx=16 + As idx=24 + BaP idx=6 简略
- 「小麦粉」own 段：Pb idx=66 + Hg idx=17 + BaP idx=7 简略
- 「玉米粉、玉米糁(渣)」own 段：Pb idx=67 + Hg idx=18 + BaP idx=8 简略

实施：
- 删 Cd idx=3, idx=4（v82-fix70 新增的 2 条复制）
- 删 BaP idx=8, idx=9, idx=10, idx=11, idx=12（v82-fix69 错加的「糙米/大米/小麦粉/玉米粉、玉米糁(渣)/稻谷」5 条复制）
"""
import re, json

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

# 1) Cd: 删 idx=3, idx=4（v82-fix70 新增）
cd = None
for t in data['contaminants']:
    if t.get('symbol') == 'Cd':
        cd = t; break
assert cd
print(f'Cd items count before: {len(cd["items"])}')
for i in [2, 3, 4, 6]:
    if i < len(cd['items']):
        print(f'  [{i}] a1_l2={cd["items"][i].get("a1_l2","")[:20]} a1_l3={cd["items"][i].get("a1_l3","")[:20]} food={cd["items"][i].get("food","")[:30]}')
# 倒序删 idx=4, idx=3
del cd['items'][4]
print(f'[DELETE Cd] position 4 (大米(粉) 复制)')
del cd['items'][3]
print(f'[DELETE Cd] position 3 (糙米 复制)')
print(f'Cd items count after: {len(cd["items"])}')

# 2) BaP: 删 idx=8, idx=9, idx=10, idx=11, idx=12（v82-fix69 错加）
bap = None
for t in data['contaminants']:
    if t.get('symbol') == 'BaP':
        bap = t; break
assert bap
print(f'\nBaP items count before: {len(bap["items"])}')
for i in range(5, min(13, len(bap['items']))):
    print(f'  [{i}] a1_l2={bap["items"][i].get("a1_l2","")[:20]} a1_l3={bap["items"][i].get("a1_l3","")[:20]} food={bap["items"][i].get("food","")[:30]}')
# 倒序删 idx=12, 11, 10, 9, 8
del bap['items'][12]
print(f'[DELETE BaP] position 12 (稻谷 错加复制)')
del bap['items'][11]
print(f'[DELETE BaP] position 11 (玉米粉、玉米糁(渣) 复制)')
del bap['items'][10]
print(f'[DELETE BaP] position 10 (小麦粉 复制)')
del bap['items'][9]
print(f'[DELETE BaP] position 9 (大米(粉) 复制)')
del bap['items'][8]
print(f'[DELETE BaP] position 8 (糙米 复制)')
print(f'BaP items count after: {len(bap["items"])}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix69[^"]*"',
    '"_last_fix": "v82-fix71-remove-dup-restate-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix69-70\][^<]*',
    '[v82-fix71] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('\nOK: v82-fix71 applied')