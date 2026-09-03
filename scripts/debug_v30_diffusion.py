import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data = json.loads(m.group(1))

# 直接查找所有 a1_l2='水产制品' 的 item
print('=== 所有 a1_l2=水产制品 的 item ===')
for c in data['contaminants']:
    for it in c.get('items', []):
        if it.get('a1_l2') == '水产制品':
            a1 = '|'.join([it.get(f'a1_l{i}', '') for i in range(1, 5)])
            print(f"  [{c['contaminant']}] food={it.get('food','')[:50]:<50} | a1=[{a1}] | a1_l3='{it.get('a1_l3','')}'")

# 然后看哪个会触发 v30
print()
print('=== v30 trigger 分析 ===')
for c in data['contaminants']:
    for it in c.get('items', []):
        a1 = [it.get(f'a1_l{i}', '') for i in range(1, 5)]
        a1f = [x for x in a1 if x]
        if len(a1f) >= 2 and a1f[1] == '水产制品':
            food = it.get('food', '') or ''
            a1l3 = it.get('a1_l3', '') or ''
            normFoodPrefix = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', food).lower()
            mountCore2 = re.sub(r'[([{【（].*$', '', a1f[1]).strip()
            mountCore2 = re.sub(r'[()（）\[\]【】:：,，.。、\s]', '', mountCore2).lower()
            isL2MultiSub = len(a1f) == 2 and not a1l3.strip() and food and mountCore2 and not normFoodPrefix.startswith(mountCore2)
            print(f"  [{c['contaminant']}] food='{food[:30]}' | a1_l3='{a1l3}' | len(a1)={len(a1f)} | normFoodPrefix='{normFoodPrefix}' | mountCore2='{mountCore2}' | isL2MultiSub={isL2MultiSub}")

# 兄弟节点探测
print()
print('=== 兄弟节点探测 (v23) 触发 ===')
print('L2 水产制品 children: 水产品罐头 / 鱼糜制品（例如：鱼丸等） / 腌制水产品 / 鱼子制品 / 熏、烤水产品 / 发酵水产品 / 其他水产制品')
for c in data['contaminants']:
    for it in c.get('items', []):
        a1 = [it.get(f'a1_l{i}', '') for i in range(1, 5)]
        a1f = [x for x in a1 if x]
        if len(a1f) >= 3 and a1f[1] == '水产制品':
            food = it.get('food', '') or ''
            # sibling探测 startPath = a1[:-1] = [水产动物及其制品, 水产制品]
            # sibCore candidates: 水产品罐头/鱼糜制品/腌制水产品/鱼子制品/熏、烤水产品/发酵水产品/其他水产制品
            sibs = ['水产品罐头', '鱼糜制品（例如：鱼丸等）', '腌制水产品', '鱼子制品', '熏、烤水产品', '发酵水产品', '其他水产制品']
            matches = []
            for s in sibs:
                sCore = re.sub(r'[([{【（].*$', '', s).strip()
                if len(sCore) < 2: continue
                # foodContainsSibCore
                escCore = re.escape(sCore)
                re_pat = re.compile(r'(^|[\(【（\[，,、\s])' + escCore)
                m1 = bool(re_pat.search(food))
                # foodContainsSibName
                escName = re.escape(s)
                re_pat2 = re.compile(r'(^|[\(【（\[，,、\s])' + escName)
                m2 = len(sCore) >= 3 and bool(re_pat2.search(food))
                if m1 or m2:
                    matches.append(s)
            if matches:
                print(f"  [{c['contaminant']}] food='{food[:30]}' → 匹配 sib: {matches}")