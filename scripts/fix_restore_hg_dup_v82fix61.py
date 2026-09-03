"""v82-fix61: 恢复 Hg idx=13-19 共 8 条 L3/L4 复制 row

用户策略：「food 有对应的内容就引用...需要你把这条，分别引用至稻谷、糙米、大米(粉)、玉米、等各个分类中去，这并不冲突」
  → 每个 L3 节点 own 段都显示 1 条 Hg row，food 字段统一用合并表达

实现：
- idx=12 保持 v82-fix60 的 L1 own row（不动）
- 在 idx=12 之后插入 8 条复制 row（idx=13..20），food 字段 = 合并表达
- 各自挂到 8 个 L3/L4 节点（与 v82-fix60 删除前的挂载点一致）
- 插入位置：idx=12 之后（position 13）
- 视觉：每个 L3 节点 own 段 1 条 Hg row；L1 own 段 1 条 Hg row
- 不会被 ancestorsLevels 重复显示（dedupKey 相同）
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

# idx=12 模板（已 v82-fix60 改为 L1 own row）
template = items[12]
print(f'[TEMPLATE] idx=12: a1_l1={template["a1_l1"]} food={template["food"][:30]}...')

# 8 个挂载点（与 v82-fix60 删除前 v82-fix59 的 idx=13-19 一致）
mounts = [
    {'a1_l2': '谷物',                'a1_l3': '玉米',                  'a1_l4': ''},          # 玉米
    {'a1_l2': '谷物',                'a1_l3': '小麦',                  'a1_l4': ''},          # 小麦
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '糙米（包括色稻米）',     'a1_l4': ''},          # 糙米
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '大米（粉）',            'a1_l4': ''},          # 大米
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '小麦粉（包括食用麸皮）', 'a1_l4': '小麦粉'},    # 小麦粉
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '玉米粉、玉米糁（渣）',   'a1_l4': '玉米粉'},    # 玉米粉
    {'a1_l2': '谷物碾磨加工品',      'a1_l3': '玉米粉、玉米糁（渣）',   'a1_l4': '玉米糁(渣)'},# 玉米糁(渣)
    {'a1_l2': '谷物',                'a1_l3': '稻谷',                  'a1_l4': ''},          # 稻谷（保持原有 idx=12 前的逻辑：稻谷也挂一份）
]
# 注意：v82-fix60 删除前的 9 条复制原本 idx=12=稻谷/13=玉米/14=小麦/15=糙米/16=大米/17=小麦粉/18=玉米粉/19=玉米糁(渣)
# 稻谷的那条就是 idx=12 自身。idx=12 现在升为 L1 own row 后稻谷节点没数据，所以最后一条 mounts[7]='稻谷' 要保留——但 idx=12 已经是 L1 own row
# 等等！我重新审视：稻谷 own 段也需要一条 Hg row
# 所以 mounts 应该 7 个：玉米/小麦/糙米/大米/小麦粉/玉米粉/玉米糁(渣)
# 稻谷靠 idx=12 的 L1 own row 继承？
# 不，L1 own row 不会继承到 L3——它只在 L1 own 段显示。
# ancestorsLevels 把 idx=12 推到 '稻谷' 节点 ancestorsLevels 第一段
# dedupKey 相同（idx=12 vs 假设的 idx=稻谷复制）会跳过
# 所以 '稻谷' own 段没 row，ancestorsLevels 显示 idx=12。
# 标题会写「上级分类 谷物及其制品... 赋予的污染物限量要求」
# 用户期望「稻谷」节点看到这条 row（不论 own 还是 ancestorsLevels），符合即可。

# 修正 mounts：删去 '稻谷'（idx=12 已经覆盖）
mounts = mounts[:-1]  # 保留 7 个

# 在 idx=12 之后（position 13）插入 7 条复制
insert_pos = 13
new_rows = []
for m_def in mounts:
    new_row = copy.deepcopy(template)
    new_row['a1_l2'] = m_def['a1_l2']
    new_row['a1_l3'] = m_def['a1_l3']
    new_row['a1_l4'] = m_def['a1_l4']
    new_rows.append(new_row)
    print(f'[INSERT] a1_l2={m_def["a1_l2"]} a1_l3={m_def["a1_l3"]} a1_l4={m_def["a1_l4"]}')

items[insert_pos:insert_pos] = new_rows
print(f'Hg items count after: {len(items)}')

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

new_content = re.sub(
    r'"_last_fix":\s*"v82-fix60[^"]*"',
    '"_last_fix": "v82-fix61-restore-hg-l3-dup-7-rows-2026-09-02"',
    new_content
)
new_content = re.sub(
    r'\[v82-fix60\][^<]*',
    '[v82-fix61] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix61 applied')