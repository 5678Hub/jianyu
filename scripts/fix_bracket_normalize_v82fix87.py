"""v82-fix87 括号归一修正
- 把 idx 中 '谷物及其制品（不包括焙烤制品）' 改为 '谷物及其制品(不包括焙烤制品)' (与 A.1 树一致)
- 把 '玉米糁(渣)' 改为 '玉米糁（渣）' (与 A.1 树一致)
"""
import json, os, shutil

DATA = 'data/gb2762/gb2762_2025.json'
BAK = 'data/gb2762/gb2762_2025.json.bak.v82fix87_brackets'

if not os.path.exists(BAK):
    shutil.copy2(DATA, BAK)
    print(f'备份: {BAK}')

with open(DATA,'r',encoding='utf-8') as f:
    d = json.load(f)

# 1. 谷物 L1 全角括号改半角 (与 A.1 树一致)
fixed1 = 0
for c in d['contaminants']:
    for it in c['items']:
        if it.get('a1_l1') == '谷物及其制品（不包括焙烤制品）':
            it['a1_l1'] = '谷物及其制品(不包括焙烤制品)'
            fixed1 += 1

print(f'修正谷物 L1 全角括号: {fixed1} 条')

# 2. 玉米糁(渣) 半角改全角 (与 A.1 树一致)
fixed2 = 0
for c in d['contaminants']:
    for it in c['items']:
        if it.get('a1_l4') == '玉米糁(渣)':
            it['a1_l4'] = '玉米糁（渣）'
            fixed2 += 1
        if it.get('a1_l3') == '玉米糁(渣)':
            it['a1_l3'] = '玉米糁（渣）'
            fixed2 += 1

print(f'修正玉米糁(渣) 半角括号: {fixed2} 条')

with open(DATA,'w',encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'已写回: {DATA}')
