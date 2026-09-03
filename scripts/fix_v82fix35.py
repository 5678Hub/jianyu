# -*- coding: utf-8 -*-
"""v82-fix35: 修正 5 个碾磨品汞克隆的 a1_l2 (谷物 -> 谷物碾磨加工品)
+ 回滚 walkExact v82-fix34 编辑 (有 Fallback B 副作用)
+ bump 版本号 v82-fix33 -> v82-fix35
"""
import re, json, os
os.chdir(r'C:\Users\10487\WorkBuddy\jianyu')

HTML_PATH = 'jianyu-standalone-v82.html'
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# ============== 1) 修正 inlineData 中 5 个克隆的 a1_l2 ==============
m = re.search(r'<script[^>]*id="inlineData"[^>]*>', html)
seg_start = m.end()
m2 = re.search(r'</script>', html[seg_start:])
seg = html[seg_start:seg_start + m2.start()]

# 解析 inlineData JSON (用括号深度跟踪,避免字符串内 } 干扰)
depth = 0
obj_end = -1
in_str = False
esc = False
BACKSLASH = chr(92)  # 反斜杠字符
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

# 找汞污染物
mercury = None
for cont in data['contaminants']:
    if cont.get('contaminant') in ('汞', '总汞'):
        mercury = cont
        break

if mercury is None:
    raise RuntimeError('未找到汞污染物')

# 5 个碾磨品克隆的 L3 名称 (tree L2="谷物碾磨加工品" 下的 L3)
mill_l3_names = {
    '糙米（包括色稻米）',
    '大米（粉）',
    '小麦粉（包括食用麸皮）',
    '玉米粉、玉米糁（渣）',
}
fixed_count = 0
for it in mercury['items']:
    if (it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）'
        and it.get('a1_l2') == '谷物'
        and it.get('a1_l3', '') in mill_l3_names
        and it.get('limit_value') == '0.02'):
        old_l2 = it['a1_l2']
        it['a1_l2'] = '谷物碾磨加工品'
        fixed_count += 1
        print(f"修正: a1_l3={it['a1_l3']!r} a1_l4={it.get('a1_l4', '')!r}  a1_l2: {old_l2!r} -> '谷物碾磨加工品'")

print(f"\n共修正 {fixed_count} 个克隆的 a1_l2")

# 写回 inlineData
new_obj = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
html = html[:seg_start] + new_obj + html[seg_start + m2.start():]

# ============== 2) 回滚 walkExact v82-fix34 编辑 ==============
v82_fix34_lines = [
    '        // v82-fix34: idx=0 时强制递归进 n.children (无论 n 是否匹配 target)',
    '        //   原因: data.a1_l1 是父类目面包屑 (如"谷物及其制品（不包括焙烤制品）"),tree 中无同名 L1,',
    '        //   但 a1_l2="谷物" 是 tree 真 L2 节点。 强制递归进 root.children 让 a1_l2 能被 walkExact 命中。',
    '        //   path 初始为 ["食品"] (root),注册 pk 统一含 "食品|" 前缀,与 sidebar pk (flattenTree 输出含 root "食品")") 一致',
    '        if (idx === 0 && !matched && n.children && path.length <= 1) {',
    '          walkExact(n.children, path.concat([n.name]), idx + 1);',
    '          continue;',
    '        }',
    '',
]
v82_fix34_block = '\n'.join(v82_fix34_lines)

if v82_fix34_block in html:
    html = html.replace(v82_fix34_block, '')
    print("回滚 walkExact v82-fix34 编辑 OK")
else:
    # 兼容性检查: 试着用 regex 匹配
    pattern = re.compile(r'        // v82-fix34:.*?        \}\n', re.DOTALL)
    if pattern.search(html):
        html = pattern.sub('', html)
        print("回滚 walkExact v82-fix34 编辑 (regex fallback) OK")
    else:
        print("警告: walkExact v82-fix34 块未找到 (可能已被回滚)")

# ============== 3) bump 版本号 v82-fix33 -> v82-fix35 ==============
old_ver = 'v82-fix33-hg-disassemble-2026-09-01'
new_ver = 'v82-fix35-clone-a1l2-fix-2026-09-01'
html = html.replace(
    f'<meta name="version" content="{old_ver}">',
    f'<meta name="version" content="{new_ver}">',
)
html = html.replace(
    f"var CACHE_BUST = '{old_ver}';",
    f"var CACHE_BUST = '{new_ver}';",
)
html = html.replace(
    '<title>[v82-fix33] GB 2762-2025',
    '<title>[v82-fix35] GB 2762-2025',
)
print(f"\nbump 版本号: {old_ver} -> {new_ver}")

# ============== 4) 写回 ==============
with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n写入完成: {HTML_PATH}")

# 验证
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    verify = f.read()
print(f"\n=== 验证 ===")
print(f"  meta version: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  CACHE_BUST: {'OK' if new_ver in verify else 'MISSING!'}")
print(f"  title: {'OK' if '[v82-fix35]' in verify else 'MISSING!'}")
print(f"  v82-fix34 残留: {'有 (问题!)' if 'v82-fix34' in verify else '无 (OK)'}")
print(f"  v82-fix33 残留: {'有 (问题!)' if 'v82-fix33' in verify else '无 (OK)'}")
