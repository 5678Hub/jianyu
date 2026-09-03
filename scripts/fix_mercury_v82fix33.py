"""v82-fix33: 修复汞 0.02 row 不应在 L2「谷物」二级
策略: 删除 a1_l2='谷物' a1_l3='' 的 8食品共用 row; 克隆 8 条到 8 个 L3/L4 节点
"""
import re, json, os
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script type="application/json" id="inlineData">', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg = html[seg_start:seg_start+m2.start()]

depth = 0; obj_end = -1; in_str = False; esc = False
for i, ch in enumerate(seg):
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
        continue
    if ch == '"': in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = i+1; break

data = json.loads(seg[:obj_end])

# 8 个目标 L3/L4 (catid 不需要, 按 name 匹配)
targets = [
        ('稻谷', ''),
        ('玉米', ''),
        ('小麦', ''),
        ('糙米（包括色稻米）', ''),
        ('大米（粉）', ''),
        ('小麦粉（包括食用麸皮）', '小麦粉'),
        ('玉米粉、玉米糁（渣）', '玉米粉'),
        ('玉米粉、玉米糁（渣）', '玉米糁(渣)'),
]

target_food = '稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉'

# 找到汞污染物
mercury = None
for cont in data['contaminants']:
    if cont.get('contaminant') == '汞' or cont.get('contaminant') == '总汞':
        mercury = cont
        print(f'找到污染物: {cont.get("contaminant")} ({cont.get("symbol")}) items={len(cont["items"])}')
        break

if mercury is None:
    raise RuntimeError('未找到汞污染物')

# 找到目标 row (a1_l2="谷物", a1_l3="", food=8 食品, limit_value="0.02")
orig_idx = -1
orig_item = None
for i, it in enumerate(mercury['items']):
    if (it.get('a1_l2') == '谷物' and
        it.get('a1_l3') == '' and
        it.get('food','') == target_food and
        it.get('limit_value') == '0.02'):
        orig_idx = i
        orig_item = it
        break

if orig_idx == -1:
    raise RuntimeError('未找到目标汞 row (a1_l2=谷物 a1_l3="" food=8 食品 limit=0.02)')

print(f'找到原 row idx={orig_idx}: a1_l1="{orig_item["a1_l1"]}" a1_l2="{orig_item["a1_l2"]}" a1_l3="{orig_item["a1_l3"]}" food={orig_item["food"]} limit={orig_item["limit_value"]}{orig_item["unit"]}')

# 克隆 8 条
new_items = []
for l3, l4 in targets:
    cloned = dict(orig_item)
    cloned['a1_l3'] = l3
    cloned['a1_l4'] = l4
    new_items.append(cloned)

# 删除原 row, 在原位置插入 8 条克隆
# 简单做法: 先 pop 原 row, 然后 extend
mercury['items'].pop(orig_idx)
# 在原位置插回 (避免污染其他污染物索引)
mercury['items'][orig_idx:orig_idx] = new_items

print(f'删除原 row 1 条, 插入克隆 row {len(new_items)} 条')

# 验证
for cloned in new_items:
    print(f'  L3="{cloned["a1_l3"]}" L4="{cloned["a1_l4"]}" food={cloned["food"][:30]}... limit={cloned["limit_value"]}{cloned["unit"]}')

# 写回 inlineData
new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start+m2.start():]

with open('jianyu-standalone-v82.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('\n写入完成: jianyu-standalone-v82.html')