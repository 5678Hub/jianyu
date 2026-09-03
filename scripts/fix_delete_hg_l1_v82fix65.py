"""v82-fix65: 删 Hg idx=12（L1 own row）

用户：「food 名称都是下级分类的内容，完全不能和 L1 级的内容相对应，就不应该出现在这里」
  → idx=12 food='稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉'
  → L1 是「谷物及其制品（不包括焙烤制品）」通用类，food 都是具体子类不匹配
  → 删 idx=12 让 ancestorsLevels 不会把它推到 L1 own 段或 L2 「谷物制品」节点

效果：
- idx=13-19 8 个 L3 own row 不动（已挂在对应 L3 节点）
- 「谷物制品」L2 节点 ancestorsLevels：仅剩 idx=63 Pb row，无 Hg
- L1 own 段：仅剩 idx=63 Pb row（删 idx=12 后无 Hg row）
- 「谷物」「谷物碾磨加工品」等 L2 节点 ancestorsLevels：仅剩 idx=63
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

hg = None
for t in data['contaminants']:
    if t.get('symbol') == 'Hg':
        hg = t; break
assert hg, 'Hg table not found'

items = hg['items']
print(f'Hg items count before: {len(items)}')

# idx=12 当前是 L1 own row（v82-fix60 改）
target = items[12]
print(f'[DELETE TARGET] idx=12 a1_l1={target["a1_l1"]} a1_l2="{target["a1_l2"]}" a1_l3="{target["a1_l3"]}" a1_l4="{target["a1_l4"]}" food={target["food"][:30]}...')
del items[12]
print(f'Hg items count after: {len(items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix64[^"]*"',
    '"_last_fix": "v82-fix65-delete-hg-l1-own-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix64\][^<]*',
    '[v82-fix65] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix65 applied')