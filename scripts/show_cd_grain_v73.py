"""列出 Cd 谷物全部 row + 模拟 L3 节点显示"""
import re, json
with open(r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    c = f.read()
m = re.search(r'<script type="application/json" id="inlineData">', c)
s = m.end()
depth = 0; in_str = False; esc = False; i = s
while i < len(c):
    ch = c[i]
    if in_str:
        if esc: esc = False
        elif ch == '\\': esc = True
        elif ch == '"': in_str = False
    else:
        if ch == '"': in_str = True
        elif ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0: e = i + 1; break
    i += 1
data = json.loads(c[s:e])

cd = None
for t in data['contaminants']:
    if t.get('symbol') == 'Cd':
        cd = t
        break

print('===== Cd 谷物 row 全部 =====')
print('idx | L2 | L3 | food | limit')
print('-' * 100)
for i, it in enumerate(cd['items']):
    if it.get('a1_l1') != '谷物及其制品（不包括焙烤制品）':
        continue
    print(f'{i:<3} | {it.get("a1_l2","")[:18]:<18} | {it.get("a1_l3","")[:18]:<18} | {it.get("food","")[:30]:<30} | {it.get("limit_value","")}')

print('\n===== 各 L3 节点 Cd 限量（最终显示）=====')
l3_nodes = [
    ('稻谷', '谷物', '稻谷'),
    ('玉米', '谷物', '玉米'),
    ('小麦', '谷物', '小麦'),
    ('大麦（包括青稞）', '谷物', '大麦（包括青稞）'),
    ('其他谷物[粟、高粱...]', '谷物', '其他谷物[例如：粟（谷子）、高粱、黑麦、燕麦、荞麦等]'),
    ('糙米（包括色稻米）', '谷物碾磨加工品', '糙米（包括色稻米）'),
    ('大米（粉）', '谷物碾磨加工品', '大米（粉）'),
    ('小麦粉（包括食用麸皮）', '谷物碾磨加工品', '小麦粉（包括食用麸皮）'),
    ('玉米粉、玉米糁（渣）', '谷物碾磨加工品', '玉米粉、玉米糁（渣）'),
    ('麦片', '谷物碾磨加工品', '麦片'),
    ('其他谷物碾磨加工品[小米...]', '谷物碾磨加工品', '其他谷物碾磨加工品（例如：小米、高粱米、大麦米、黍米等）'),
]

# 模拟挂载
def find_own(l2, l3):
    matches = []
    for i, it in enumerate(cd['items']):
        if it.get('a1_l1') != '谷物及其制品（不包括焙烤制品）':
            continue
        if it.get('a1_l2') == l2 and it.get('a1_l3') == l3:
            matches.append((i, it))
    return matches

def find_l2(l2):
    matches = []
    for i, it in enumerate(cd['items']):
        if it.get('a1_l1') != '谷物及其制品（不包括焙烤制品）':
            continue
        if it.get('a1_l2') == l2 and not it.get('a1_l3'):
            matches.append((i, it))
    return matches

for name, l2, l3 in l3_nodes:
    own = find_own(l2, l3)
    l2_only = find_l2(l2)
    print(f'\n【{name}】')
    print(f'  本级 ({len(own)} 条):')
    for i, it in own:
        print(f'    [{i}] {it["food"][:40]:<40} {it["limit_value"]}')
    if name in ['稻谷', '糙米（包括色稻米）', '大米（粉）']:
        # idx=1「谷物碾磨加工品〔糙米、大米（粉）除外〕」是通类，但适用「谷物」L2 而非「谷物碾磨加工品」L2
        # 检查 idx=0（谷物通类）是否适用
        if l2 == '谷物':
            print(f'  ancestorsLevels (idx=0 谷物〔稻谷除外〕0.1 适用，因 {name} ≠ 稻谷)')
        elif l2 == '谷物碾磨加工品':
            # idx=1 0.1 不适用糙米/大米
            excluded = ['糙米（包括色稻米）', '大米（粉）']
            if name in excluded:
                print(f'  ancestorsLevels (idx=1 谷物碾磨加工品〔糙米、大米（粉）除外〕0.1 不适用，{name} 在除外列表中)')
            else:
                print(f'  ancestorsLevels (idx=1 谷物碾磨加工品〔糙米、大米（粉）除外〕0.1 适用)')
    else:
        # 检查 ancestorsLevels
        if l2 == '谷物':
            print(f'  ancestorsLevels (idx=0 谷物〔稻谷除外〕0.1 适用)')
        elif l2 == '谷物碾磨加工品':
            print(f'  ancestorsLevels (idx=1 谷物碾磨加工品〔糙米、大米（粉）除外〕0.1 适用)')