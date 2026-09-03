"""v82-fix63: 删 Hg idx=20 + idx=18/19 a1_l4 清空

用户：「19和20 是一个分类...节点，对应 food 字段。而不是 food 字段去拆分成各个节点」
  → idx=19 '玉米粉' 和 idx=20 '玉米糁(渣)' 都挂在 A.1 L3 '玉米粉、玉米糁（渣）' 节点下
  → 但 walkExact 在 a1_l4='玉米粉'/'玉米糁(渣)' 时找不到 A.1 L4 子节点（树里没列）
  → Fallback B 让两者都注册到 L3 → '玉米粉、玉米糁（渣）' L3 节点 own 段显示 2 条 Hg row（重复）

A.1 树相关 L3 节点（grep 结果）：
  L3: 小麦粉（包括食用麸皮）/ 大米（粉）/ 玉米粉、玉米糁（渣）/ 糙米（包括色稻米）
  → 没有 L4 子节点

修复：
- 删 idx=20（idx=19 的 L4 复制，walkExact 都 fall back 到同一 L3）
- idx=18 a1_l4='小麦粉' → ''（A.1 树没 '小麦粉' L4，字段无意义）
- idx=19 a1_l4='玉米粉' → ''（同上）

最终 idx=12-19 共 8 条 row：
  idx=12 L1 own / idx=13 稻谷 / idx=14 玉米 / idx=15 小麦 /
  idx=16 糙米（包括色稻米） / idx=17 大米（粉） / idx=18 小麦粉（包括食用麸皮） / idx=19 玉米粉、玉米糁（渣）
  全部 a1_l4=''，注册到 L3 节点
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

# 检查 idx=18/19/20
print(f'[idx=18] a1_l3={items[18].get("a1_l3","")} a1_l4="{items[18].get("a1_l4","")}" food={items[18].get("food","")[:30]}')
print(f'[idx=19] a1_l3={items[19].get("a1_l3","")} a1_l4="{items[19].get("a1_l4","")}" food={items[19].get("food","")[:30]}')
print(f'[idx=20] a1_l3={items[20].get("a1_l3","")} a1_l4="{items[20].get("a1_l4","")}" food={items[20].get("food","")[:30]}')

# 1) idx=18 a1_l4 清空
items[18]['a1_l4'] = ''
print(f'[UPDATE] idx=18 a1_l4=""')

# 2) idx=19 a1_l4 清空
items[19]['a1_l4'] = ''
print(f'[UPDATE] idx=19 a1_l4=""')

# 3) 删 idx=20
del items[20]
print(f'[DELETE] idx=20 (玉米糁(渣) L4 复制)')

print(f'Hg items count after: {len(items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix62[^"]*"',
    '"_last_fix": "v82-fix63-remove-hg-l4-dup-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix62\][^<]*',
    '[v82-fix63] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix63 applied')