import re, json
with open('jianyu-standalone-v82.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取内联 JS 函数
def extract_function(name, source):
    pattern = rf'function {name}\(.*?^\}}'
    m = re.search(pattern, source, re.DOTALL | re.MULTILINE)
    return m.group(0) if m else ''

# 先抽出 inlineData
m = re.search(r'<script type="application/json" id="inlineData">(.*?)</script>', content)
data_json = m.group(1)

# 直接手写关键函数（不依赖源 JS）
def norm(s):
    return (s or '').replace(',，、;；', '').replace('()()[]【】]+', '').replace(':：+', '').replace('\s+', '').lower()

def pathKey(path):
    return '|'.join(path)

def getExcludes(food):
    s = (food or '').toString() if hasattr(food, 'toString') else str(food)
    idx = s.rfind('除外')
    if idx < 0: return []
    openIdx = -1; depth = 0
    for i in range(idx - 1, -1, -1):
        if s[i] in '))）': depth += 1
        elif s[i] in '(（':
            if depth == 0: openIdx = i; break
            depth -= 1
    if openIdx < 0: return []
    excludeStr = s[openIdx + 1:idx]
    return [e for e in re.split(r'[、,,及和\s]+', excludeStr) if e]

def sibIsExcluded(sibName, excludes):
    if not excludes: return False
    sibNorm = sibName.replace('[()）【】:：,,。、]', '').lower().strip()
    for e in excludes:
        if sibNorm == e: return True
        if len(e) >= 3 and (sibNorm.startswith(e) or e.startswith(sibNorm)): return True
    return False

def foodContainsSibCore(food, sibCore):
    if not food or not sibCore: return False
    escCore = re.escape(sibCore)
    re_pat = re.compile(r'(^|[\(【（\[，,、\s])' + escCore)
    return bool(re_pat.search(food))

def foodContainsSibName(food, sibName):
    if not food or not sibName: return False
    escName = re.escape(sibName)
    re_pat = re.compile(r'(^|[\(【（\[，,、\s])' + escName)
    return bool(re_pat.search(food))

data = json.loads(data_json)

# 构造 tree
tree = data['appendix_a1']['tree']

def find_by_path(tree, path):
    node = None
    for p in path:
        children = node['children'] if node else tree
        if not children: return None
        node = next((c for c in children if c['name'] == p), None)
        if not node: return None
    return node

def find_by_name(tree, name):
    if tree['name'] == name: return tree
    for c in tree.get('children', []) or []:
        r = find_by_name(c, name)
        if r: return r
    return None

# 模拟 buildItemIndex
itemIndex = {}

for c in data['contaminants']:
    for it in c['items']:
        paths = []  # 直接用 a1_l 路径
        a1 = [it.get(f'a1_l{i}', '') for i in range(1, 5)]
        a1 = [x for x in a1 if x]
        if a1:
            paths.append(a1)

        enriched = dict(it)
        enriched['_contaminant'] = c['contaminant']
        enriched['_symbol'] = c.get('symbol', '')
        enriched['_table_no'] = c.get('table_no', '')

        for path in paths:
            pk = pathKey(path)
            if pk not in itemIndex:
                itemIndex[pk] = []
            arr = itemIndex[pk]
            dupKey = f"{c.get('table_no','')}\x01{it.get('food','')}\x01{it.get('limit_value','')}\x01{it.get('sub_value','')}\x01{it.get('main_remark','')}\x01{it.get('sub_remark','')}\x01{it.get('note','')}"
            if any(x.get('_dupKey') == dupKey for x in arr): continue
            enriched['_dupKey'] = dupKey
            arr.append(dict(enriched))

            # v23/v29 兄弟节点探测 (path.length >= 3)
            # v30 L2 通类项扩散 (path.length == 2 且 food 不以 L2 mountCore 开头)
            food = it.get('food', '') or ''
            normFoodPrefix = food.replace('[()）【】:：,,。、\s]', '').lower()
            mountName2 = path[1] if len(path) >= 2 else ''
            mountCore2 = re.sub(r'[([{【（].*$', '', mountName2).strip().replace('[()）【】:：,,。、\s]', '').lower()
            isL2MultiSub = len(path) == 2 and not (it.get('a1_l3') or '').strip() and food and mountCore2 and not normFoodPrefix.startswith(mountCore2)
            if (len(path) >= 3 or isL2MultiSub) and food:
                startPath = path if isL2MultiSub else path[:-1]
                startNode = find_by_path(tree, startPath)
                if startNode and startNode.get('children'):
                    currentLeaf = None if isL2MultiSub else path[-1]
                    excludes = getExcludes(food)
                    for sib in startNode['children']:
                        if not isL2MultiSub and sib['name'] == currentLeaf: continue
                        if not sib.get('name') or len(sib['name']) < 2: continue
                        if sibIsExcluded(sib['name'], excludes): continue
                        sibCore = re.sub(r'[([{【（].*$', '', sib['name']).strip()
                        if not sibCore or len(sibCore) < 2: continue
                        if foodContainsSibCore(food, sibCore) or (len(sibCore) >= 3 and foodContainsSibName(food, sib['name'])):
                            sibPath = startPath + [sib['name']]
                            sibPk = pathKey(sibPath)
                            if sibPk not in itemIndex:
                                itemIndex[sibPk] = []
                            sibArr = itemIndex[sibPk]
                            if any(x.get('_dupKey') == dupKey for x in sibArr): continue
                            itemIndex[sibPk].append(dict(enriched))

# 输出 idx 中几个关键节点的 row
def show_idx(path):
    pk = pathKey(path)
    items = itemIndex.get(pk, [])
    print(f"\nidx[{path}]: {len(items)} 条")
    for it in items:
        a1 = '|'.join([it.get(f'a1_l{i}', '') for i in range(1, 5)])
        print(f"  [{it['_contaminant']}] food={it.get('food', '')[:50]} | a1=[{a1}] | limit={it.get('limit_value')}")

show_idx(['水产动物及其制品'])
show_idx(['水产动物及其制品', '鲜、冻水产动物'])
show_idx(['水产动物及其制品', '鲜、冻水产动物', '鱼类'])
show_idx(['水产动物及其制品', '鲜、冻水产动物', '鱼类', '非肉食性鱼类'])
show_idx(['水产动物及其制品', '水产制品'])
show_idx(['水产动物及其制品', '水产制品', '鱼糜制品（例如：鱼丸等）'])
show_idx(['水产动物及其制品', '水产制品', '海蜇制品'])
show_idx(['水产动物及其制品', '水产制品', '鱼类制品'])
show_idx(['水产动物及其制品', '水产制品', '其他鱼类制品'])
show_idx(['水产动物及其制品', '水产制品', '其他水产品'])