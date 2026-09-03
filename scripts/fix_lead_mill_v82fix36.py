# -*- coding: utf-8 -*-
"""v82-fix36: 修复 L2 谷物碾磨加工品 铅 Pb 0.5 row 下沉到 4 个 L3
策略: 与 v82-fix33/v82-fix35 汞 row 同样的拆分处理
"""
import re, json, os
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

HTML_PATH = 'jianyu-standalone-v82.html'
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# ============== 1) 解析 inlineData ==============
m = re.search(r'<script[^>]*id="inlineData"[^>]*>', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg = html[seg_start:seg_start + m2.start()]

depth = 0
obj_end = -1
in_str = False
esc = False
BACKSLASH = chr(92)
QUOTE = '"'
for i, ch in enumerate(seg):
    if in_str:
        if esc:
            esc = False
        elif ch == BACKSLASH:
            esc = True
        elif ch == QUOTE:
            in_str = False
        continue
    if ch == QUOTE:
        in_str = True
    elif ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            obj_end = i + 1
            break

data = json.loads(seg[:obj_end])

# ============== 2) 找铅污染物 ==============
lead = None
for cont in data['contaminants']:
    if cont.get('contaminant') == '铅' or cont.get('symbol') == 'Pb':
        lead = cont
        print(f"找到污染物: {cont.get('contaminant')} ({cont.get('symbol')}) items={len(cont['items'])}")
        break

if lead is None:
    raise RuntimeError('未找到铅污染物')

# ============== 3) 找到目标 row (idx=64) ==============
# a1_l1='谷物及其制品（不包括焙烤制品）' a1_l2='谷物碾磨加工品' a1_l3=''
# food='糙米、大米、小麦粉、玉米粉、玉米糁等' limit=0.5
target_food = '糙米、大米、小麦粉、玉米粉、玉米糁等'
orig_idx = -1
orig_item = None
for i, it in enumerate(lead['items']):
    if (it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）'
        and it.get('a1_l2') == '谷物碾磨加工品'
        and it.get('a1_l3', '') == ''
        and it.get('food', '') == target_food
        and it.get('limit_value') == '0.5'):
        orig_idx = i
        orig_item = it
        break

if orig_idx == -1:
    raise RuntimeError('未找到目标铅 row (a1_l2=谷物碾磨加工品 a1_l3="" food=5 食品 limit=0.5)')

print(f'找到原 row idx={orig_idx}: a1_l1={orig_item["a1_l1"]!r} a1_l2={orig_item["a1_l2"]!r} a1_l3={orig_item["a1_l3"]!r}')
print(f'  food={orig_item["food"]} limit={orig_item["limit_value"]}{orig_item["unit"]}')

# ============== 4) 克隆 4 条到 4 个 L3 ==============
# 4 个 L3 名称 (与 tree L2 谷物碾磨加工品 下的 L3 名称一致, 玉米粉+玉米糁共用 L3)
targets = [
    '糙米（包括色稻米）',
    '大米（粉）',
    '小麦粉（包括食用麸皮）',
    '玉米粉、玉米糁（渣）',
]
new_items = []
for l3 in targets:
    cloned = dict(orig_item)
    cloned['a1_l3'] = l3
    cloned['a1_l4'] = ''  # tree L3 无 children
    new_items.append(cloned)
    print(f'  克隆: a1_l3={l3!r}')

# ============== 5) 删除原 row, 插入 4 条克隆 ==============
lead['items'].pop(orig_idx)
lead['items'][orig_idx:orig_idx] = new_items
print(f'\n删除原 row 1 条, 插入克隆 row {len(new_items)} 条')

# ============== 6) 写回 inlineData ==============
new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start + m2.start():]

# ============== 7) bump 版本号 v82-fix35 -> v82-fix36 ==============
old_ver = 'v82-fix35-clone-a1l2-fix-2026-09-01'
new_ver = 'v82-fix36-lead-mill-disassemble-2026-09-01'
html = html.replace(
    f'<meta name="version" content="{old_ver}">',
    f'<meta name="version" content="{new_ver}">',
)
html = html.replace(
    f"var CACHE_BUST = '{old_ver}';",
    f"var CACHE_BUST = '{new_ver}';",
)
html = html.replace(
    '<title>[v82-fix35] GB 2762-2025',
    '<title>[v82-fix36] GB 2762-2025',
)
print(f'\nbump 版本号: {old_ver} -> {new_ver}')

# ============== 8) 写回 HTML ==============
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\n写入完成: {HTML_PATH}')

# 验证
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    verify = f.read()
print(f"\n=== 验证 ===")
print(f"  meta version: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  CACHE_BUST: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  title: {'OK' if '[v82-fix36]' in verify else 'MISSING!'}")
print(f"  v82-fix35 残留: {'有 (问题!)' if 'v82-fix35' in verify else '无 (OK)'}")
