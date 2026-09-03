# -*- coding: utf-8 -*-
"""v82-fix38: 修复 L2 谷物本级 limit=— 的总汞 8 食品 row (idx=20)
v82-fix33 误把 limit=— row 保留 (脚本只删 limit=0.02 那条, 这条 limit=— 没匹配, 漏删)
按 v82-fix33 用户原意"汞 row 不应在 L2 谷物二级中", 此处删除 idx=20
0.02 限量已在 8 个 L3 row 拆分就位
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

# ============== 2) 删除汞 idx=20 limit=— row ==============
mercury = None
for cont in data['contaminants']:
    if cont.get('contaminant') == '汞' or cont.get('symbol') == 'Hg':
        mercury = cont
        break

if mercury is None:
    raise RuntimeError('未找到汞污染物')

target_idx = -1
for i, it in enumerate(mercury['items']):
    if (it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）'
        and it.get('a1_l2') == '谷物'
        and it.get('a1_l3', '') == ''
        and it.get('food', '') == '稻谷、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉'
        and it.get('limit_value') == '—'):
        target_idx = i
        break

if target_idx == -1:
    raise RuntimeError('未找到目标汞 row (a1_l2=谷物 a1_l3="" food=8 食品 limit=—)')

print(f'找到目标汞 row idx={target_idx}:')
print(f'  a1_l1={mercury["items"][target_idx]["a1_l1"]!r}')
print(f'  a1_l2={mercury["items"][target_idx]["a1_l2"]!r}')
print(f'  a1_l3={mercury["items"][target_idx]["a1_l3"]!r}')
print(f'  food={mercury["items"][target_idx]["food"]}')
print(f'  limit={mercury["items"][target_idx]["limit_value"]} has_limit={mercury["items"][target_idx]["has_limit"]}')

mercury['items'].pop(target_idx)
print(f'\n已删除 idx={target_idx} row')

# ============== 3) 写回 inlineData ==============
new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start + m2.start():]

# ============== 4) bump 版本号 v82-fix37 -> v82-fix38 ==============
old_ver = 'v82-fix37-baijiu-flatten-2026-09-01'
new_ver = 'v82-fix38-hg-l2-empty-fix-2026-09-01'
html = html.replace(
    f'<meta name="version" content="{old_ver}">',
    f'<meta name="version" content="{new_ver}">',
)
html = html.replace(
    f"var CACHE_BUST = '{old_ver}';",
    f"var CACHE_BUST = '{new_ver}';",
)
html = html.replace(
    '<title>[v82-fix37] GB 2762-2025',
    '<title>[v82-fix38] GB 2762-2025',
)
print(f'\nbump 版本号: {old_ver} -> {new_ver}')

# ============== 5) 写回 HTML ==============
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\n写入完成: {HTML_PATH}')

# 验证
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    verify = f.read()
print(f"\n=== 验证 ===")
print(f"  meta version: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  CACHE_BUST: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  title: {'OK' if '[v82-fix38]' in verify else 'MISSING!'}")
print(f"  v82-fix37 残留: {'有 (问题!)' if 'v82-fix37' in verify else '无 (OK)'}")
