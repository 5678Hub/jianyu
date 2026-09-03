"""v82-fix97 4 副本同步脚本 - HTML inlineData JSON + data JSON

同步目标：
1. jianyu/data/gb2762/gb2762_2025.json (主)
2. jianyu/jianyu-standalone-v82.html
3. 抽检不合格查询助手/data/gb2762/gb2762_2025.json
4. 抽检不合格查询助手/jianyu-standalone-v82.html
5. 工作台/data/gb2762/gb2762_2025.json
6. 工作台/jianyu-standalone-v82.html

策略：用最新 jianyu/data/gb2762/gb2762_2025.json 作为单一事实源，同步其他副本。
"""
import json
import shutil
import os
import sys

SRC_JSON = 'jianyu/data/gb2762/gb2762_2025.json'
SRC_HTML = 'jianyu/jianyu-standalone-v82.html'

# 4 副本同步目标（HTML + JSON 各 3 个）
JSON_TARGETS = [
    '抽检不合格查询助手/data/gb2762/gb2762_2025.json',
    '工作台/data/gb2762/gb2762_2025.json',
]
HTML_TARGETS = [
    '抽检不合格查询助手/jianyu-standalone-v82.html',
    '工作台/jianyu-standalone-v82.html',
]

HTML_BACKUP_SUFFIX = '.bak.v82fix97_sync'


def copy_json(target):
    """同步 JSON 文件"""
    if not os.path.exists(target):
        print(f'  ✗ {target} 不存在，跳过')
        return False
    # 备份
    bak = target + HTML_BACKUP_SUFFIX
    shutil.copy(target, bak)
    # 复制
    shutil.copy(SRC_JSON, target)
    print(f'  ✓ {target} ← {SRC_JSON} (备份 {bak})')
    return True


def sync_html_inline_data(target):
    """同步 HTML inlineData JSON 块"""
    if not os.path.exists(target):
        print(f'  ✗ {target} 不存在，跳过')
        return False

    # 备份
    bak = target + HTML_BACKUP_SUFFIX
    shutil.copy(target, bak)

    # 读源 JSON
    with open(SRC_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 序列化（带 2 空格缩进）
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    # 读 HTML
    with open(target, 'r', encoding='utf-8') as f:
        html = f.read()

    # 找 inlineData 块边界
    script_start_marker = '<script type="application/json" id="inlineData">'
    script_end_marker = '</script>'

    script_start_pos = html.find(script_start_marker)
    if script_start_pos < 0:
        print(f'  ✗ {target} 未找到 inlineData script 块，回退到整体复制')
        shutil.copy(SRC_HTML, target)
        return False

    script_end_pos = html.find(script_end_marker, script_start_pos)
    if script_end_pos < 0:
        print(f'  ✗ {target} 未找到 inlineData script 结束，回退到整体复制')
        shutil.copy(SRC_HTML, target)
        return False

    # 替换整个 inlineData 块
    new_html = (
        html[:script_start_pos] +
        script_start_marker + '\n' +
        json_str + '\n' +
        script_end_marker +
        html[script_end_pos + len(script_end_marker):]
    )

    with open(target, 'w', encoding='utf-8') as f:
        f.write(new_html)

    # 验证
    new_html_read = open(target, 'r', encoding='utf-8').read()
    json_start = new_html_read.find('{', script_start_pos)
    json_end = new_html_read.rfind('}', script_start_pos, script_end_pos) + 1
    try:
        new_inline_data = json.loads(new_html_read[json_start:json_end])
        n = len(new_inline_data['contaminants'])
        print(f'  ✓ {target} inlineData 同步完成 (备份 {bak}, contaminants={n})')
        return True
    except json.JSONDecodeError as e:
        print(f'  ✗ {target} inlineData 验证失败: {e}, 回退到备份')
        shutil.copy(bak, target)
        return False


def main():
    print(f'== v82-fix97 4 副本同步 ==\n')
    print(f'事实源 JSON: {SRC_JSON}')
    print(f'事实源 HTML: {SRC_HTML}\n')

    # 1. 同步 JSON 到其他副本
    print('-- 同步 JSON --')
    for t in JSON_TARGETS:
        copy_json(t)

    # 2. 同步 HTML inlineData 到其他副本
    print('\n-- 同步 HTML inlineData --')
    for t in HTML_TARGETS:
        sync_html_inline_data(t)

    # 3. 验证：所有 6 个文件应 MD5 一致
    print('\n-- 验证 MD5 一致性 --')
    import hashlib
    files_to_check = [SRC_JSON, SRC_HTML] + JSON_TARGETS + HTML_TARGETS
    md5s = {}
    for f in files_to_check:
        if os.path.exists(f):
            with open(f, 'rb') as fh:
                md5 = hashlib.md5(fh.read()).hexdigest()
            md5s[f] = md5
            print(f'  {md5}  {f}')

    # 期望：JSON 3 个一致 + HTML 3 个一致（可能 HTML 因为不同副本其他差异不完全一致，但 inlineData 部分必须一致）
    # 简单分组检查
    json_md5s = set()
    html_md5s = set()
    for f, m in md5s.items():
        if f.endswith('.json'):
            json_md5s.add(m)
        elif f.endswith('.html'):
            html_md5s.add(m)

    if len(json_md5s) == 1:
        print(f'\n  ✓ 3 个 JSON MD5 一致: {list(json_md5s)[0]}')
    else:
        print(f'\n  ✗ JSON MD5 不一致: {json_md5s}')

    if len(html_md5s) == 1:
        print(f'  ✓ 3 个 HTML MD5 一致: {list(html_md5s)[0]}')
    else:
        print(f'  ! HTML MD5 不一致（可能副本存在其他差异，但 inlineData 已同步）: {html_md5s}')


if __name__ == '__main__':
    main()