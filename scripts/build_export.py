"""打包 jianyu 源码 + 数据库供外部审查（ChatGPT 等）"""
import os, zipfile

ROOT = r"C:\Users\10487\WorkBuddy\jianyu"
OUT = r"C:\Users\10487\WorkBuddy\jianyu_source_export.zip"

EXCLUDE_FILES = {'install_jianyu.ps1', 'serve.py', 'start-jianyu.bat', 'master.xlsx'}
EXCLUDE_DIRS = {'.git'}

def should_include(rel_unix):
    bn = os.path.basename(rel_unix)
    # 排除临时文件（_ 开头）
    if bn.startswith('_'):
        return False
    if bn in EXCLUDE_FILES:
        return False
    parts = rel_unix.split('/')
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    return True

# 白名单确保核心齐全
REQUIRED = [
    'index.html', 'README.md', 'manifest.webmanifest', 'sw.js', 'icon.svg',
    'docs/JSON_SCHEMA.md',
    'data/master.json',
    'data/categories_2026.json',
    'data/categories_2026_full.json',
    'data/categories_subcat.json',
    'data/category_map.json',
    'data/subcat_to_items.json',
    'data/synonyms.json',
    'scripts/rebuild_index.py',
    'scripts/unify_meta.py',
    'scripts/build_export.py',
]
# current_period 子目录
for f in sorted(os.listdir(os.path.join(ROOT, 'data', 'current_period'))):
    if not f.startswith('_'):
        REQUIRED.append('data/current_period/' + f)
required_set = set(REQUIRED)

count = 0; size = 0
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for rel_unix in REQUIRED:
        fp = os.path.join(ROOT, *rel_unix.split('/'))
        if os.path.exists(fp) and should_include(rel_unix):
            z.write(fp, rel_unix); count += 1; size += os.path.getsize(fp)
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            full = os.path.join(root, fn)
            rel_unix = os.path.relpath(full, ROOT).replace(os.sep, '/')
            if rel_unix in required_set:
                continue
            if should_include(rel_unix):
                z.write(full, rel_unix); count += 1; size += os.path.getsize(full)

print(f'✅ 打包完成: {count} 个文件, {size/1024:.1f} KB')
print(f'输出: {OUT}')

# 验证无重复
with zipfile.ZipFile(OUT) as z:
    names = z.namelist()
    dup = [n for n in set(names) if names.count(n) > 1]
    print(f'去重文件数: {len(set(names))}  重复: {dup if dup else "无"}')
    print()
    print('=== 文件清单 ===')
    for n in sorted(set(names)):
        print(f'  {n}')