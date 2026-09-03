"""v82-fix82: 同步 data/gb2762/gb2762_2025.json → jianyu-standalone-v82.html inlineData

HTML inlineData 在 line 587-11880
文件读取：先备份 → 把 inlineData 替换为最新 JSON → 写回
"""
import json
import shutil
from pathlib import Path

HTML = 'jianyu-standalone-v82.html'
DATA = 'data/gb2762/gb2762_2025.json'
BACKUP = 'jianyu-standalone-v82.html.bak.v82fix82_inline_data'

# 备份
if not Path(BACKUP).exists():
    shutil.copy2(HTML, BACKUP)
    print(f'备份: {BACKUP}')

# 读取最新 JSON
with open(DATA, 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# 序列化（保持缩进 2 字符与原 inlineData 一致）
new_inline = json.dumps(new_data, ensure_ascii=False, indent=2)

# 读 HTML
with open(HTML, 'r', encoding='utf-8') as f:
    html = f.read()

# 找 inlineData 范围
start_marker = '<script type="application/json" id="inlineData">'
end_marker = '</script>'

start_idx = html.index(start_marker) + len(start_marker)
end_idx = html.index(end_marker, start_idx)

old_inline = html[start_idx:end_idx]
print(f'旧 inlineData 长度: {len(old_inline)} 字节')
print(f'新 inlineData 长度: {len(new_inline)} 字节')

# 替换
new_html = html[:start_idx] + '\n' + new_inline + '\n' + html[end_idx:]

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f'已写回: {HTML}')
print(f'新 HTML 大小: {len(new_html)} 字节')

# 验证
with open(HTML, 'r', encoding='utf-8') as f:
    verify = f.read()
import re
m = re.search(r'<script type="application/json" id="inlineData">', verify)
i = m.end()
depth = 0
start = i
end2 = i
while i < len(verify):
    if verify[i] == '{': depth += 1
    elif verify[i] == '}':
        depth -= 1
        if depth == 0: end2 = i + 1; break
    i += 1
parsed = json.loads(verify[start:end2])
total = sum(len(con['items']) for con in parsed['contaminants'])
print(f'验证: total items = {total}')
