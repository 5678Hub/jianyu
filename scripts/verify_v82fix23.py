import json, re
with open('C:/Users/10487/WorkBuddy/jianyu/data/gb2762/gb2762_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
tree = data['appendix_a1']['tree']
contaminants = data['contaminants']

def norm(s):
    s = s or ''
    s = re.sub(r'[,,\u3001;;\uff1b]+', '', s)
    s = re.sub(r'[()\uff08\uff09\[\]\u3010\u3011]+', '', s)
    s = re.sub(r'[:\uff1a]+', '', s)
    s = re.sub(r'\s+', '', s)
    return s.lower()

item_index = {}
def register(pk, item):
    if pk not in item_index: item_index[pk] = []
    item_index[pk].append(item)

def key(p):
    return '|'.join(norm(x) for x in p)

def find_node(t, name):
    for n in t:
        if norm(n['name']) == norm(name): return n
    return None

def norm_prefix(s):
    return re.sub(r'[()（）\[\]【】:：,,。、\s]', '', s or '').lower()

def get_excludes(food):
    s = food or ''
    idx = s.rfind('除外')
    if idx < 0: return []
    depth = 0; open_idx = -1
    for i in range(idx - 1, -1, -1):
        c = s[i]
        if c in '）)': depth += 1
        elif c in '（(':
            if depth == 0: open_idx = i; break
            depth -= 1
    if open_idx < 0: return []
    excl = s[open_idx+1:idx]
    parts = re.split(r'[、,,]', excl)
    return [re.sub(r'[()（）\[\]【】:：,,。、]', '', p).lower().strip() for p in parts if p.strip()]

def sib_is_excluded(sib_name, excludes):
    sib_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', sib_name).lower().strip()
    sib_core = sib_name.split('(')[0].split('（')[0].strip()
    sib_core_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', sib_core).lower().strip()
    for e in excludes:
        if not e or len(e) < 2: continue
        if sib_norm == e: return True
        if sib_core_norm == e: return True
        if len(e) >= 3 and (sib_norm.startswith(e) or e.startswith(sib_norm)): return True
    return False

def food_contains(food, sib_core):
    if not food or not sib_core: return False
    esc = re.escape(sib_core)
    return bool(re.search(r'(^|[\(【（\[，,、\s])' + esc, food))

for c in contaminants:
    for it in c.get('items', []):
        if c.get('contaminant') != '铅': continue
        a1l1 = it.get('a1_l1','') or ''
        a1l2 = it.get('a1_l2','') or ''
        a1l3 = it.get('a1_l3','') or ''
        a1l4 = it.get('a1_l4','') or ''
        node = find_node(tree, a1l1) if a1l1 else None
        if not node: continue
        path = [a1l1]
        if a1l2:
            node2 = None
            for c2 in node.get('children', []):
                if norm(c2['name']) == norm(a1l2) or (norm(c2['name']).startswith(norm(a1l2)) and len(norm(a1l2)) >= 3):
                    node2 = c2; break
            if not node2: continue
            path.append(node2['name'])
            node = node2
            if a1l3:
                node3 = None
                for c3 in node.get('children', []):
                    if norm(c3['name']) == norm(a1l3) or (norm(c3['name']).startswith(norm(a1l3)) and len(norm(a1l3)) >= 3):
                        node3 = c3; break
                if not node3: continue
                path.append(node3['name'])
                node = node3
        pk = key(path)
        register(pk, it)
        if len(path) == 2 and not a1l3.strip() and it.get('food'):
            mount_name = path[1]
            mount_core = mount_name.split('(')[0].split('（')[0].strip()
            mount_core_n = norm_prefix(mount_core)
            food_n = norm_prefix(it.get('food',''))
            is_l2_multi_sub = mount_core_n and not food_n.startswith(mount_core_n)
            if is_l2_multi_sub:
                startNode = node
                if startNode and startNode.get('children'):
                    excludes = get_excludes(it.get('food',''))
                    for sib in startNode['children']:
                        if sib_is_excluded(sib['name'], excludes): continue
                        sibCore = sib['name'].split('(')[0].split('（')[0].strip()
                        if not sibCore or len(sibCore) < 2: continue
                        if food_contains(it.get('food',''), sibCore) or (len(sibCore) >= 3 and food_contains(it.get('food',''), sib['name'])):
                            sibPath = path + [sib['name']]
                            sibPk = key(sibPath)
                            register(sibPk, it)

def is_applicable(item, cpath):
    food = item.get('food','')
    a1_path = [item.get('a1_l1',''), item.get('a1_l2',''), item.get('a1_l3',''), item.get('a1_l4','')]
    a1_path = [x for x in a1_path if x]
    ancestor_level = len(a1_path)
    if ancestor_level == 0: return True
    idx = food.rfind('除外')
    if idx >= 0:
        depth = 0; open_idx = -1
        for i in range(idx - 1, -1, -1):
            ch = food[i]
            if ch in '）)': depth += 1
            elif ch in '（(':
                if depth == 0: open_idx = i; break
                depth -= 1
        if open_idx >= 0:
            excl = food[open_idx+1:idx]
            parts = re.split(r'[、,,]', excl)
            for p in parts:
                p_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', p).lower().strip()
                if not p_norm or len(p_norm) < 2: continue
                for nm in cpath:
                    nm_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', nm).lower().strip()
                    nm_core = nm.split('(')[0].split('（')[0].strip()
                    nm_core = re.sub(r'[()（）\[\]【】:：,,。、]', '', nm_core).lower().strip()
                    if nm_norm == p_norm or nm_core == p_norm: return False
    if len(cpath) == ancestor_level:
        mount_name = a1_path[ancestor_level - 1]
        mount_core = mount_name.split('(')[0].split('（')[0].strip()
        mount_core_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', mount_core).lower().strip()
        food_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', food).lower().strip()
        if food_norm and not food_norm.startswith(mount_core_norm):
            return True
    elif len(cpath) > ancestor_level:
        mount_name = a1_path[ancestor_level - 1]
        mount_core = mount_name.split('(')[0].split('（')[0].strip()
        mount_core_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', mount_core).lower().strip()
        food_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', food).lower().strip()
        if food_norm and not food_norm.startswith(mount_core_norm):
            food_cores = re.split(r'[,，、]+', food_norm)
            food_cores = [re.sub(r'[(（].*$', '', c).strip() for c in food_cores if c.strip() and len(c.strip()) >= 2]
            for nm in cpath:
                nm_norm = re.sub(r'[()（）\[\]【】:：,,。、]', '', nm).lower().strip()
                for fc in food_cores:
                    if nm_norm == fc: return True
            return False
    return True

def ancestors_levels(path):
    res = []
    pk = key(path)
    prim_keys = set((it.get('_table_no',''), it.get('food',''), it.get('limit_value',''), it.get('sub_value','')) for it in item_index.get(pk, []))
    for i in range(len(path) - 2, -1, -1):
        a_path = path[:i+1]
        a_key = key(a_path)
        if a_key == pk: continue
        items = item_index.get(a_key, [])
        anc_name = path[i]
        filtered = [it for it in items if is_applicable(it, a_path)]
        filtered = [it for it in filtered if (it.get('_table_no',''), it.get('food',''), it.get('limit_value',''), it.get('sub_value','')) not in prim_keys]
        if filtered:
            res.append((anc_name, [(it.get('food',''), it.get('limit_value','')) for it in filtered]))
    return res

l3_juice = ['饮料类', '果蔬汁类及其饮料(例如:苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等)', '果蔬汁（浆）']
l3_drink = ['饮料类', '果蔬汁类及其饮料(例如:苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等)', '果蔬汁（浆）类饮料']
l3_conc = ['饮料类', '果蔬汁类及其饮料(例如:苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等)', '浓缩果蔬汁（浆）']
l2_juice = ['饮料类', '果蔬汁类及其饮料(例如:苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等)']

print('=== L3 「果蔬汁（浆)」 详情页 ===')
print('本级:')
for it in item_index.get(key(l3_juice), []):
    print(f'  {it.get("food","")[:40]:<40} | {it.get("limit_value","")}')
print('上级分类:')
for a, items in ancestors_levels(l3_juice):
    print(f'  ({a}):')
    for food, lim in items:
        print(f'    {food[:40]:<40} | {lim}')

print()
print('=== L3 「果蔬汁（浆）类饮料」 详情页 ===')
print('本级:')
for it in item_index.get(key(l3_drink), []):
    print(f'  {it.get("food","")[:40]:<40} | {it.get("limit_value","")}')
print('上级分类:')
for a, items in ancestors_levels(l3_drink):
    print(f'  ({a}):')
    for food, lim in items:
        print(f'    {food[:40]:<40} | {lim}')

print()
print('=== L3 「浓缩果蔬汁（浆)」 详情页 ===')
print('本级:')
for it in item_index.get(key(l3_conc), []):
    print(f'  {it.get("food","")[:40]:<40} | {it.get("limit_value","")}')
print('上级分类:')
for a, items in ancestors_levels(l3_conc):
    print(f'  ({a}):')
    for food, lim in items:
        print(f'    {food[:40]:<40} | {lim}')

print()
print('=== L2 「果蔬汁类及其饮料」 详情页 ===')
print('本级:')
for it in item_index.get(key(l2_juice), []):
    print(f'  {it.get("food","")[:40]:<40} | {it.get("limit_value","")}')