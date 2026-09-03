"""v82-fix93 HTML 同步脚本 - 同步 inlineData JSON

注意：v82-fix92 同步 HTML 时插入了 7 个 A.1 节点 + 8 条 row 的 block 在错位置
（缺 , 分隔），导致 inlineData JSON 解析失败。

修复策略：用最新的 data/gb2762/gb2762_2025.json 直接覆盖整个 inlineData 块。
"""
import json
import shutil

HTML = 'jianyu-standalone-v82.html'
JSON_FILE = 'data/gb2762/gb2762_2025.json'
HTML_BACKUP = 'jianyu-standalone-v82.html.bak.v82fix93'

def main():
    # 备份 HTML
    shutil.copy(HTML, HTML_BACKUP)
    print(f'备份 → {HTML_BACKUP}')

    # 读 JSON
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 序列化（带 2 空格缩进，与原 HTML 风格一致）
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    # 读 HTML
    with open(HTML, 'r', encoding='utf-8') as f:
        html = f.read()

    # 找 inlineData 块边界
    script_start_marker = '<script type="application/json" id="inlineData">'
    script_end_marker = '</script>'

    script_start_pos = html.find(script_start_marker)
    if script_start_pos < 0:
        raise RuntimeError('未找到 inlineData script 块')

    # inlineData 块的结束（</script> 位置）
    script_end_pos = html.find(script_end_marker, script_start_pos)
    if script_end_pos < 0:
        raise RuntimeError('未找到 inlineData script 结束')

    # 替换整个 inlineData 块
    new_html = (
        html[:script_start_pos] +
        script_start_marker + '\n' +
        json_str + '\n' +
        script_end_marker +
        html[script_end_pos + len(script_end_marker):]
    )

    with open(HTML, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f'✓ {HTML} 同步完成')
    print(f'  inlineData 块: {script_start_pos} ~ {script_end_pos + len(script_end_marker)}')

    # 验证：解析新内嵌 JSON
    new_html_read = open(HTML, 'r', encoding='utf-8').read()
    script_start = new_html_read.find(script_start_marker)
    script_end = new_html_read.find(script_end_marker, script_start)
    json_start = new_html_read.find('{', script_start)
    json_end = new_html_read.rfind('}', script_start, script_end) + 1
    new_inline_data = json.loads(new_html_read[json_start:json_end])
    print(f'  验证解析成功: contaminants={len(new_inline_data["contaminants"])}')

    # 验证 L3 熟制坚果 row
    found = 0
    for c in new_inline_data['contaminants']:
        for row in c['items']:
            if row.get('a1_l3') == '熟制坚果及籽类（带壳、脱壳、包衣）':
                found += 1
                print(f'  ✓ T{c["table_no"]} {c["contaminant"]} {row["food"]} {row["limit_value"]} {row["unit"]}')
    print(f'  L3 熟制坚果 row 数: {found}')

if __name__ == '__main__':
    main()
