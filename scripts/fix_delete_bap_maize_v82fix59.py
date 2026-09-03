"""v82-fix59: 删除 BaP idx=5（玉米 L3 own row），消除与 idx=6 合并表达入口在 L3 玉米下的重复

策略来源：用户截图 + 「不拆出来，原文是什么就是什么」
本次仅删截图直接证明的 idx=5；其他 L3/L4 own rows 列出供用户决策。
"""
import re, json

SRC = r'C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'<script type="application/json" id="inlineData">', content)
start = m.end()
depth = 0
i = start
in_string = False
escape = False
while i < len(content):
    c = content[i]
    if in_string:
        if escape:
            escape = False
        elif c == '\\':
            escape = True
        elif c == '"':
            in_string = False
    else:
        if c == '"':
            in_string = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    i += 1

data = json.loads(content[start:end])

# 找 BaP table
bap = None
for t in data['contaminants']:
    if t.get('symbol') == 'BaP':
        bap = t
        break
assert bap, 'BaP table not found'

# 找 idx=5（玉米 own row）—— 没有 idx 字段，按位置
items = bap['items']
print(f'BaP items count before: {len(items)}')

target_idx = None
for i, it in enumerate(items):
    if it.get('a1_l3') == '玉米' and it.get('food') == '玉米' and it.get('limit') == '2.0 μg/kg':
        target_idx = i
        print(f'[FOUND] position={i} food={it["food"]} l3={it["a1_l3"]} limit={it["limit"]}')
        break

assert target_idx is not None, 'Target BaP 玉米 row not found'

# 删除
del items[target_idx]
print(f'[DELETE] position={target_idx}')
print(f'BaP items count after: {len(items)}')

# 写回：bump 版本号 + 重写 inlineData
new_json = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# 替换原 inlineData 内容
old_block = content[start:end]
new_content = content[:start] + new_json + content[end:]

# bump 版本号（同时改 _last_fix、title、cache_bust）
# _last_fix
new_content = re.sub(
    r'"_last_fix":\s*"v82-fix58[^"]*"',
    '"_last_fix": "v82-fix59-delete-bap-maize-own-row-2026-09-02"',
    new_content
)
# title
new_content = re.sub(
    r'\[v82-fix58\][^<]*',
    '[v82-fix59] GB 2762-2025 食品中污染物限量查询 · jianyu',
    new_content
)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('OK: v82-fix59 applied')