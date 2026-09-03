import re, json, sys

with open('C:/Users/10487/WorkBuddy/jianyu/jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', html, re.DOTALL)
raw = m.group(1)
data = json.loads(raw)

# Search all contaminants items for animal oils a1 path
print('=== ALL items with a1_l2 mentioning 动物 OR 鱼油 OR 磷虾 ===')
count = 0
for c in data['contaminants']:
    for it in c['items']:
        s = json.dumps(it, ensure_ascii=False)
        if ('动物' in s and '油' in s) or ('鱼油' in it.get('food','')) or ('磷虾' in it.get('food','')):
            count += 1
            if count <= 30:
                print(f'\ntable_no={c["table_no"]} {c["contaminant"]}/{c["symbol"]}')
                print(f'  food: {it.get("food")}')
                print(f'  a1_l1: {it.get("a1_l1")}')
                print(f'  a1_l2: {it.get("a1_l2")}')
                print(f'  a1_l3: {it.get("a1_l3")}')
                print(f'  a1_l4: {it.get("a1_l4")}')
                print(f'  sub_label: {it.get("sub_label")} sub_value: {it.get("sub_value")} lim: {it.get("limit_value")}')
print(f'\nTotal matches: {count}')

# What does the 油脂制品 L3 其他油脂制品 currently have for arsenic
print('\n\n=== items in a1_l3="其他油脂制品" ===')
for c in data['contaminants']:
    for it in c['items']:
        if it.get('a1_l3') == '其他油脂制品':
            print(f'  {c["contaminant"]}/{it.get("sub_label","")} → {it.get("food")} lim={it.get("limit_value")} sub={it.get("sub_value")}')

# Show ALL arsenic items a1 paths involving 油 / 脂
print('\n=== arsenic items with 油 / 脂 in path ===')
for c in data['contaminants']:
    if c['contaminant'] != '砷':
        continue
    for it in c['items']:
        path = [it.get('a1_l1',''), it.get('a1_l2',''), it.get('a1_l3',''), it.get('a1_l4','')]
        joined = ' > '.join([x for x in path if x])
        if '油' in joined or '脂' in joined:
            print(f'  [{joined}]')
            print(f'    food={it.get("food")} lim={it.get("limit_value")} sub_label={it.get("sub_label")} sub_val={it.get("sub_value")}')
