"""v82-fix60: Hg idx=12 升为 L1 own row + 删 idx=13-19 共 8 条复制

用户策略：「不拆出来，原文是什么就是什么」「食品分类不需要改」
  food='稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉'

实现：idx=12 改 a1_l2='' a1_l3='' a1_l4=''（L1 own row），挂到 '谷物及其制品...'
  副作用：L1 own 段会显示 idx=12（标题"谷物及其制品...的污染物限量要求"）；
          L1 所有 L3 叶子节点的 ancestorsLevels 第一段也会显示这条 row。
  walkExact 注册到 pk(['谷物及其制品（不包括焙烤制品）'])
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

# 找 Hg table
hg = None
for t in data['contaminants']:
    if t.get('symbol') == 'Hg':
        hg = t; break
assert hg, 'Hg table not found'

items = hg['items']
print(f'Hg items count before: {len(items)}')

# 1) 改 idx=12 的 a1_l2='' a1_l3='' a1_l4=''
it12 = items[12]
print(f'[idx=12 BEFORE] a1_l1={it12.get("a1_l1","")} a1_l2={it12.get("a1_l2","")} a1_l3={it12.get("a1_l3","")} a1_l4={it12.get("a1_l4","")}')
it12['a1_l2'] = ''
it12['a1_l3'] = ''
it12['a1_l4'] = ''
print(f'[idx=12 AFTER]  a1_l1={it12.get("a1_l1","")} a1_l2="{it12.get("a1_l2","")}" a1_l3="{it12.get("a1_l3","")}" a1_l4="{it12.get("a1_l4","")}"')

# 2) 删 idx=13-19 共 8 条（positions 13..19，倒序删）
to_delete = list(range(13, 20))  # 13,14,15,16,17,18,19
print(f'[DELETE] positions: {to_delete}')
for idx in reversed(to_delete):
    del items[idx]
    print(f'  deleted pos={idx}')

print(f'Hg items count after: {len(items)}')

# 写回：bump 版本号 + 重写 inlineData
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix59[^"]*"',
    '"_last_fix": "v82-fix60-delete-hg-dup-8-rows-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix59\][^<]*',
    '[v82-fix60] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix60 applied')