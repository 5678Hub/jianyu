# -*- coding: utf-8 -*-
"""v82-fix37: 酒类 L1 下,删除 L3 '白酒' 假节点 + 铅 0.5 row 下挂到 L2 蒸馏酒 本级
策略:
  1) tree[15] 酒类 > 蒸馏酒 > children 中删除 L3 '白酒' 节点
  2) 铅 Pb idx=73 a1_l4='白酒' -> '' (a1Path 缩短为 ['酒类', '蒸馏酒...'],注册到 L2 本级)
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

# ============== 2) 删除 tree L3 '白酒' 节点 ==============
tree = data['appendix_a1']['tree']
# 找 L1 酒类
l1 = None
for n in tree:
    if n['name'] == '酒类':
        l1 = n
        break
if l1 is None:
    raise RuntimeError('未找到 L1 酒类')

# 找 L2 蒸馏酒
l2 = None
for n in l1.get('children', []):
    if '蒸馏酒' in n['name']:
        l2 = n
        break
if l2 is None:
    raise RuntimeError('未找到 L2 蒸馏酒')

# 删除 L3 白酒
l3_white_spirit = None
l3_filtered = [c for c in l2.get('children', []) if c.get('name') != '白酒']
if len(l3_filtered) < len(l2.get('children', [])):
    l3_white_spirit = next((c for c in l2['children'] if c.get('name') == '白酒'), None)
    l2['children'] = l3_filtered
    print(f"已从 tree L2 蒸馏酒 下删除 L3 '白酒' 节点 (剩余 L3: {len(l3_filtered)})")
else:
    print("警告: tree 中未找到 L3 '白酒' 节点 (可能已被删除)")

# ============== 3) 铅 Pb idx=73 a1_l4 清空 ==============
lead = None
for cont in data['contaminants']:
    if cont.get('contaminant') == '铅' or cont.get('symbol') == 'Pb':
        lead = cont
        break

if lead is None:
    raise RuntimeError('未找到铅污染物')

target_idx = -1
for i, it in enumerate(lead['items']):
    if (it.get('a1_l1') == '酒类'
        and '蒸馏酒' in it.get('a1_l2', '')
        and it.get('a1_l3', '') == ''
        and it.get('a1_l4', '') == '白酒'
        and it.get('food', '') == '白酒'
        and it.get('limit_value') == '0.5'):
        target_idx = i
        break

if target_idx == -1:
    raise RuntimeError('未找到目标铅 row (a1_l4=白酒 food=白酒 limit=0.5)')

print(f'\n找到目标铅 row idx={target_idx}:')
print(f'  原 a1_l2={lead["items"][target_idx]["a1_l2"]!r}')
print(f'  原 a1_l3={lead["items"][target_idx]["a1_l3"]!r}')
print(f'  原 a1_l4={lead["items"][target_idx]["a1_l4"]!r}')

# 修改 a1_l4
lead['items'][target_idx]['a1_l4'] = ''
print(f'  新 a1_l4="" (下挂到 L2 蒸馏酒 本级)')

# ============== 4) 写回 inlineData ==============
new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start + m2.start():]

# ============== 5) bump 版本号 v82-fix36 -> v82-fix37 ==============
old_ver = 'v82-fix36-lead-mill-disassemble-2026-09-01'
new_ver = 'v82-fix37-baijiu-flatten-2026-09-01'
html = html.replace(
    f'<meta name="version" content="{old_ver}">',
    f'<meta name="version" content="{new_ver}">',
)
html = html.replace(
    f"var CACHE_BUST = '{old_ver}';",
    f"var CACHE_BUST = '{new_ver}';",
)
html = html.replace(
    '<title>[v82-fix36] GB 2762-2025',
    '<title>[v82-fix37] GB 2762-2025',
)
print(f'\nbump 版本号: {old_ver} -> {new_ver}')

# ============== 6) 写回 HTML ==============
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\n写入完成: {HTML_PATH}')

# 验证
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    verify = f.read()
print(f"\n=== 验证 ===")
print(f"  meta version: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  CACHE_BUST: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  title: {'OK' if '[v82-fix37]' in verify else 'MISSING!'}")
print(f"  v82-fix36 残留: {'有 (问题!)' if 'v82-fix36' in verify else '无 (OK)'}")
