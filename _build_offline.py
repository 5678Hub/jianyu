"""构建 jianyu-offline.html 单文件离线版
- 读取 index.html
- 把 fetch('data/xxx.json') 改为 window.__JIANYU_DATA__['xxx'] 同步读
- 把 data/ 所有 JSON 内联到 <script>window.__JIANYU_DATA__ = {...}</script>
"""
import re, json, pathlib

ROOT = pathlib.Path(r'C:\Users\10487\WorkBuddy\jianyu')
INDEX = ROOT / 'index.html'
OUT = ROOT / 'jianyu-offline.html'

DATA_FILES = [
    ('master', ROOT / 'data' / 'master.json'),
    ('category_map', ROOT / 'data' / 'category_map.json'),
    ('subcat_to_items', ROOT / 'data' / 'subcat_to_items.json'),
    ('gb_checklist_subcat', ROOT / 'data' / 'current_period' / 'gb_checklist_subcat.json'),
    ('categories_2026', ROOT / 'data' / 'categories_2026.json'),
    ('gb2762', ROOT / 'data' / 'gb2762' / 'gb2762_2025.json'),
]

html = INDEX.read_text(encoding='utf-8')

# 替换 fetch 块为同步读 window.__JIANYU_DATA__
old_block = """async function loadData() {
  try {
    const [master, cm, subcatItems, subcatChecklist, categories] = await Promise.all([
      fetch('data/master.json').then(r => r.json()),
      fetch('data/category_map.json').then(r => r.json()),
      fetch('data/subcat_to_items.json').then(r => r.json()),
      fetch('data/current_period/gb_checklist_subcat.json').then(r => r.json()),
      fetch('data/categories_2026.json').then(r => r.json()),
    ]);"""

new_block = """function loadData() {
  try {
    // 单文件离线版:数据从 window.__JIANYU_DATA__ 同步读取(无 fetch)
    const D = window.__JIANYU_DATA__;
    const master = D.master;
    const cm = D.category_map;
    const subcatItems = D.subcat_to_items;
    const subcatChecklist = D.gb_checklist_subcat;
    const categories = D.categories_2026;"""

if old_block not in html:
    raise SystemExit('ERROR: loadData block not found in index.html — 模板已变更,需手动调整')

html = html.replace(old_block, new_block)

# 末尾 `await Promise.all` 已经替换,接下来是赋值,我们已经把 `await Promise.all` 删了,
# 但 html 里 Promise.all 之后还有 `]);\n` 之类残留。检查替换后的 html。

# 找 Promise.all 之后到 `state.records = master.records || [];` 的内容,清理多余符号
# 实际原代码:`]);\n    state.records = ...` — 我们的 new_block 已经把 `]);\n` 后内容用 `state.records = ...` 接上
# 不需要额外处理。

# 替换 title（标记为离线版）
html = html.replace(
    '<title>jianyu · 食品抽检风险查询</title>',
    '<title>jianyu · 食品抽检风险查询（离线版）</title>',
    1
)

# 在 head 加注释（说明构建时间和数据快照）
build_note = f'  <!-- 单文件离线版 · 构建于 2026-08-14 · 数据快照见末尾 window.__JIANYU_DATA__._meta -->\n'
html = html.replace(
    '<meta name="theme-color" content="#1a365d">',
    build_note + '<meta name="theme-color" content="#1a365d">',
    1
)

# 构建数据 JSON
data_obj = {}
total_size = 0
for key, path in DATA_FILES:
    if not path.exists():
        print(f'  WARN: missing {path}')
        continue
    data_obj[key] = json.loads(path.read_text(encoding='utf-8'))
    size = path.stat().st_size
    total_size += size
    print(f'  + {key}: {size/1024:.1f} KB')

data_json = json.dumps(data_obj, ensure_ascii=False, separators=(',', ':'))

# 在 </body> 前插入 window.__JIANYU_DATA__
inject = f"""
<script>
// 单文件离线版数据载荷 (构建于 2026-08-14)
window.__JIANYU_DATA__ = {data_json};
</script>
"""
html = html.replace('</body>', inject + '</body>', 1)

OUT.write_text(html, encoding='utf-8')
out_size = OUT.stat().st_size
print(f'\nOFFLINE 总大小: {out_size/1024/1024:.2f} MB')
print(f'数据载荷: {len(data_json)/1024/1024:.2f} MB')
print(f'  含 master={sum(1 for _ in data_obj["master"]["records"])} records')
print(f'  含 gb2762={sum(len(c["items"]) for c in data_obj["gb2762"]["contaminants"])} 限量记录')
print(f'已写入: {OUT}')