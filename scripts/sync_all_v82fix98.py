"""v82-fix98 全量同步：JSON → 所有 HTML inlineData + 其他副本 JSON

同步目标：
- jianyu/data/gb2762/gb2762_2025.json (主)
- jianyu/jianyu-standalone-v82.html
- jianyu/gb2762.html
- 抽检不合格查询助手/data/gb2762/gb2762_2025.json
- 抽检不合格查询助手/jianyu-standalone-v82.html
- 工作台/data/gb2762/gb2762_2025.json
- 工作台/jianyu-standalone-v82.html

策略：用最新 JSON 整体覆盖所有 HTML 的 inlineData 块，并复制 JSON 到其他副本。
对 gb2762.html 额外更新 CACHE_BUST 与 meta version。
"""
import json
import shutil
import os
import hashlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKBUDDY = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_JSON = os.path.join(WORKBUDDY, 'jianyu', 'data', 'gb2762', 'gb2762_2025.json')
TARGETS = {
    'jianyu-standalone-v82.html': [
        os.path.join(WORKBUDDY, 'jianyu', 'jianyu-standalone-v82.html'),
        os.path.join(WORKBUDDY, '抽检不合格查询助手', 'jianyu-standalone-v82.html'),
        os.path.join(WORKBUDDY, '工作台', 'jianyu-standalone-v82.html'),
    ],
    'gb2762.html': [os.path.join(WORKBUDDY, 'jianyu', 'gb2762.html')],
}
JSON_TARGETS = [
    os.path.join(WORKBUDDY, '抽检不合格查询助手', 'data', 'gb2762', 'gb2762_2025.json'),
    os.path.join(WORKBUDDY, '工作台', 'data', 'gb2762', 'gb2762_2025.json'),
]


def sync_json(target):
    if not os.path.exists(target):
        print(f'  ✗ {target} 不存在')
        return False
    shutil.copy(target, target + '.bak.v82fix98_sync')
    shutil.copy(SRC_JSON, target)
    print(f'  ✓ {target}')
    return True


def sync_html(html_path, update_cache_bust=False):
    if not os.path.exists(html_path):
        print(f'  ✗ {html_path} 不存在')
        return False
    shutil.copy(html_path, html_path + '.bak.v82fix98_sync')

    with open(SRC_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    marker_open = '<script type="application/json" id="inlineData">'
    marker_close = '</script>'
    start = html.find(marker_open)
    end = html.find(marker_close, start)
    if start < 0 or end < 0:
        print(f'  ✗ {html_path} 未找到 inlineData 块')
        return False

    new_html = html[:start] + marker_open + '\n' + json_str + '\n' + marker_close + html[end + len(marker_close):]

    if update_cache_bust:
        new_html = new_html.replace('v82-fix82-revert-idx88-multi-mount-2026-09-02', 'v82-fix98-meat-fish-2026-09-03')
        new_html = new_html.replace("var CACHE_BUST = 'v82-fix56-delete-idx68-grain-0-5-2026-09-02';",
                                    "var CACHE_BUST = 'v82-fix98-meat-fish-2026-09-03';")

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

    # 验证
    with open(html_path, 'r', encoding='utf-8') as f:
        verify_html = f.read()
    v_start = verify_html.find(marker_open)
    v_end = verify_html.find(marker_close, v_start)
    v_json_start = verify_html.find('{', v_start)
    v_json_end = verify_html.rfind('}', v_start, v_end) + 1
    try:
        parsed = json.loads(verify_html[v_json_start:v_json_end])
        print(f'  ✓ {html_path} (contaminants={len(parsed["contaminants"])})')
        return True
    except json.JSONDecodeError as e:
        print(f'  ✗ {html_path} 验证失败: {e}')
        return False


def md5(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def main():
    print('== v82-fix98 全量同步 ==\n')

    print('-- 同步 JSON --')
    for t in JSON_TARGETS:
        sync_json(t)

    print('\n-- 同步 HTML inlineData --')
    for source_name, paths in TARGETS.items():
        update_cb = (source_name == 'gb2762.html')
        for p in paths:
            sync_html(p, update_cache_bust=update_cb)

    print('\n-- MD5 验证 --')
    files = [SRC_JSON, 'jianyu/jianyu-standalone-v82.html', 'jianyu/gb2762.html'] + \
            JSON_TARGETS + TARGETS['jianyu-standalone-v82.html']
    for f in files:
        if os.path.exists(f):
            print(f'  {md5(f)}  {f}')


if __name__ == '__main__':
    main()
