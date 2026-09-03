import re, json, os
os.chdir(r'C:\Users/WorkBuddy/jianyu') if False else os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

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

# 列出所有污染物名
print('所有污染物:', [c.get('contaminant','') for c in data['contaminants']])

# L1=谷物及其制品(不包括焙烤制品) 下所有 row
l1_options = ['谷物及其制品（不包括焙烤制品）', '谷物及其制品(不包括焙烤制品)']
print('\n' + '=' * 90)
print('L1 谷物及其制品(不包括焙烤制品) 下 全部 row (按污染物分, 含 limit_value)')
print('=' * 90)
from collections import defaultdict
by_cont = defaultdict(list)
for cont in data['contaminants']:
    for it in cont['items']:
        if it.get('a1_l1') in l1_options:
            by_cont[cont.get('contaminant','')].append(it)

for cont_name in sorted(by_cont.keys()):
    items = by_cont[cont_name]
    print(f'\n【{cont_name}】({len(items)} 条)')
    for idx, it in enumerate(items):
        l2 = it.get('a1_l2','')
        l3 = it.get('a1_l3','')
        l4 = it.get('a1_l4','')
        food = it.get('food','')
        lv = it.get('limit_value','')
        unit = it.get('unit','')
        symbol = it.get('symbol','')
        # 标记 a1_l3 空 且 food 含 8 食品共用字符串
        flag = ''
        if l3 == '' and ('稻谷' in food and '玉米' in food and '小麦' in food):
            flag = '  ⚠️ 8食品共用-应下沉'
        elif l3 == '' and food and food not in ('谷物', '谷物(稻谷除外)'):
            flag = '  ⚠️ a1_l3空'
        print(f'  #{idx+1:2d} L2="{l2}" L3="{l3}" L4="{l4}" | {symbol} {lv}{unit} | food={food[:55]}{flag}')

# 单独提取"8 食品共用"的所有 row (任何污染物)
print('\n' + '=' * 90)
print('[汇总] 8 食品共用 row (food="稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉")')
print('=' * 90)
target_food = '稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉'
for cont in data['contaminants']:
    for idx, it in enumerate(cont['items']):
        if it.get('food','') == target_food:
            print(f'  污染物={cont.get("contaminant","")}({cont.get("symbol","")}) '
                  f'a1_l2="{it.get("a1_l2","")}" a1_l3="{it.get("a1_l3","")}" '
                  f'limit={it.get("limit_value","")}{it.get("unit","")}')