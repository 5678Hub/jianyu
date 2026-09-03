"""v82-fix68: 恢复 Pb idx=68「麦片、面筋、粥类罐头、带馅(料)面米制品」0.5

用户：「恢复」
  → v82-fix56 时删除的 idx=68（麦片、面筋、粥类罐头、带馅(料)面米制品 0.5 row）恢复
  → PDF 表 1 谷物碾磨加工品列：麦片、面筋、粥类罐头、带馅(料)面米制品 0.5

挂载点选择（按 A.1 树结构）：
  - 「麦片」L3（谷物碾磨加工品下）→ 0.5 row 挂这
  - 「面筋」/「粥类罐头」/「带馅(料)面米制品」是「其他谷物制品[例如：带馅（料）面米制品、粥类罐头等]」L3 的例子
  → 实际 A.1 树中：
    - 「谷物碾磨加工品」L2 下有「麦片」L3
    - 「谷物制品」L2 下有「其他谷物制品[例如：...]」L3（含面筋/粥类罐头/带馅面米制品）
  → 「面筋」「粥类罐头」「带馅(料)面米制品」是「其他谷物制品」L3 节点示例，但 A.1 树 L3 名只到「其他谷物制品[例如：...]」
  → Fallback B 同 v82-fix63：a1_l4='面筋' 等字段 fall back 到 L3 「其他谷物制品」

策略：
- idx=68 挂「麦片」L3 a1_l3='麦片' a1_l4=''（A.1 树有「麦片」L3 子节点）
- 副作用：「面筋」「粥类罐头」「带馅(料)面米制品」不在 A.1 树 L3 子节点中（归在「其他谷物制品[例如：...]」L3），
  → 但 idx=68 是合并表达 row，a1_l4='面筋' 等字段 Fallback B 退化到「其他谷物制品[例如：...]」L3
  → 实际应保持 idx=68 整体作为「麦片」L3 own row，不挂其他 L3（其他 L3 没专属 0.5 row 是因为 PDF 表达合并）

最终实现：
- idx=68 a1_l2='谷物碾磨加工品' a1_l3='麦片' a1_l4=''
- food='麦片、面筋、粥类罐头、带馅(料)面米制品'（PDF 表 1 原文）
- limit=0.5
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

pb = None
for t in data['contaminants']:
    if t.get('symbol') == 'Pb':
        pb = t; break
assert pb, 'Pb table not found'

items = pb['items']
print(f'Pb items count before: {len(items)}')

# 在 idx=67 后插入 idx=68（v82-fix56 删的位置）
template = items[63]  # idx=63 Pb L1 own row 模板
new_row = {
    'food': '麦片、面筋、粥类罐头、带馅(料)面米制品',
    'pollutant': '铅',
    'limit_value': '0.5',
    'has_limit': True,
    'sub_value': '',
    'unit': 'mg/kg',
    'note': '',
    'modif': '',
    'inspection_method': 'GB 5009.12',
    'a1_l1': '谷物及其制品（不包括焙烤制品）',
    'a1_l2': '谷物碾磨加工品',
    'a1_l3': '麦片',
    'a1_l4': '',
}
items.insert(68, new_row)
print(f'[INSERT] idx=68 a1_l3=麦片 food=麦片、面筋、粥类罐头、带馅(料)面米制品 0.5')

print(f'Pb items count after: {len(items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix65[^"]*"',
    '"_last_fix": "v82-fix68-restore-pb-maipian-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix65\][^<]*',
    '[v82-fix68] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix68 applied')