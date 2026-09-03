#!/usr/bin/env python3
"""v82-fix89 HTML 内嵌数据同步：补 5 条新 row 到 HTML 内嵌的 gb2762_2025 数据"""
import re
import json

with open('jianyu-standalone-v82.html', encoding='utf-8') as f:
    html = f.read()

# 5 个锚点（每个污染物表中的特定 row）
anchor1 = '''          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "铅",
          "limit_value": "1.0",
          "has_limit": true,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "",
          "modif": "",
          "inspection_method": "GB 5009.12",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "其他食用菌制品",
          "a1_l4": ""
        },'''

new1 = '''        {
          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "铅",
          "limit_value": "1.0",
          "has_limit": true,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "",
          "modif": "",
          "inspection_method": "GB 5009.12",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "新鲜食用菌（未经加工的、经表面处理的、预切的、冷冻的食用菌）",
          "a1_l3": "银耳",
          "a1_l4": ""
        },
'''

anchor2 = '''          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "镉",
          "limit_value": "0.5",
          "has_limit": true,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "",
          "modif": "干重计",
          "inspection_method": "GB 5009.15",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "",
          "a1_l4": "木耳制品"
        },'''

new2 = '''        {
          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "镉",
          "limit_value": "0.5",
          "has_limit": true,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "",
          "modif": "干重计",
          "inspection_method": "GB 5009.15",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "其他食用菌制品",
          "a1_l4": ""
        },
'''

anchor3 = '''          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "总汞",
          "limit_value": "—",
          "has_limit": false,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "",
          "modif": "",
          "inspection_method": "GB 5009.17",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "其他食用菌制品",
          "a1_l4": ""
        },'''

new3 = '''        {
          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "总汞",
          "limit_value": "—",
          "has_limit": false,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "",
          "modif": "",
          "inspection_method": "GB 5009.17",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "银耳",
          "a1_l4": ""
        },
'''

anchor4 = '''          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "甲基汞 a",
          "limit_value": "0.1",
          "has_limit": true,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "a",
          "modif": "干重计",
          "inspection_method": "GB 5009.17",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "其他食用菌制品",
          "a1_l4": ""
        },'''

new4 = '''        {
          "food": "木耳及其制品、银耳及其制品",
          "pollutant": "甲基汞 a",
          "limit_value": "0.1",
          "has_limit": true,
          "sub_value": "",
          "unit": "mg/kg",
          "note": "a",
          "modif": "干重计",
          "inspection_method": "GB 5009.17",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "银耳",
          "a1_l4": ""
        },
'''

anchor5 = '''          "food": "木耳及其制品、银耳及其制品",
          "limit": "— mg/kg",
          "limit_value": "—",
          "has_limit": false,
          "limit_modifier": "",
          "main_label": "总砷",
          "main_remark": "",
          "sub_label": "无机砷 a",
          "sub_limit": "0.5 mg/kg",
          "sub_value": "0.5",
          "sub_has_limit": true,
          "sub_modifier": "(干重计)",
          "sub_remark": "a",
          "remark": "",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "新鲜食用菌（未经加工的、经表面处理的、预切的、冷冻的食用菌）",
          "a1_l3": "银耳",
          "a1_l4": "",
          "inspection_method": "GB 5009.11",
          "test_method": ""
        },'''

new5 = '''        {
          "food": "木耳及其制品、银耳及其制品",
          "limit": "— mg/kg",
          "limit_value": "—",
          "has_limit": false,
          "limit_modifier": "",
          "main_label": "总砷",
          "main_remark": "",
          "sub_label": "无机砷 a",
          "sub_limit": "0.5 mg/kg",
          "sub_value": "0.5",
          "sub_has_limit": true,
          "sub_modifier": "(干重计)",
          "sub_remark": "a",
          "remark": "",
          "a1_l1": "食用菌及其制品",
          "a1_l2": "食用菌制品",
          "a1_l3": "其他食用菌制品",
          "a1_l4": "",
          "inspection_method": "GB 5009.11",
          "test_method": ""
        },
'''

# 检查锚点
for name, anchor in [('锚点1', anchor1), ('锚点2', anchor2), ('锚点3', anchor3), ('锚点4', anchor4), ('锚点5', anchor5)]:
    cnt = html.count(anchor)
    print(f'{name}: {cnt} 处')

# 备份
import shutil
shutil.copy('jianyu-standalone-v82.html', 'jianyu-standalone-v82.html.bak.v82fix89_pre_sync')

# 在每个锚点后插入新 row
inserts = [
    (anchor1, new1),
    (anchor2, new2),
    (anchor3, new3),
    (anchor4, new4),
    (anchor5, new5),
]

for anchor, new in inserts:
    pos = html.find(anchor)
    if pos == -1:
        print(f'[SKIP] 锚点未找到')
        continue
    # 在锚点结束后插入
    insert_pos = pos + len(anchor)
    html = html[:insert_pos] + '\n' + new + html[insert_pos:]
    print(f'[OK] 在 pos {insert_pos} 后插入新 row')

with open('jianyu-standalone-v82.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('\nHTML 同步完成')
