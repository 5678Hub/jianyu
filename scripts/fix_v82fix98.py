"""v82-fix98: 修复熏烧烤 L3 孤节点 + 肉食性鱼类甲基汞通类 row

1. 删除 A.1 树中 L2「肉制品（包括内脏制品、血制品）」下的 L3 孤节点「熏、烧、烤肉类」
   （保留 L4「熟肉制品 > 熏、烧、烤肉类」）
2. T3 甲基汞通类 row 复制挂载到 L4「肉食性鱼类（例如：金枪鱼、金目鲷、枪鱼、鲨鱼等）」
   原 row: food='肉食性鱼类及其制品(金枪鱼、金目鲷、枪鱼及以上鱼类的制品、鲨鱼及以上鱼类的制品除外)', a1_l3='鱼类', a1_l4=''
   复制 row: a1_l3='鱼类', a1_l4='肉食性鱼类（例如：金枪鱼、金目鲷、枪鱼、鲨鱼等）'
"""
import json
import shutil
import os
import sys

JSON_PATH = 'data/gb2762/gb2762_2025.json'


def main():
    bak = JSON_PATH + '.bak.v82fix98'
    shutil.copy(JSON_PATH, bak)
    print(f'备份: {bak}')

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. 删除 L3 孤节点「熏、烧、烤肉类」
    removed = False
    for root in data['appendix_a1']['tree']:
        if root['name'] == '肉及肉制品':
            for l2 in root.get('children', []):
                if l2['name'] == '肉制品（包括内脏制品、血制品）':
                    before = len(l2.get('children', []))
                    l2['children'] = [c for c in l2.get('children', []) if c['name'] != '熏、烧、烤肉类']
                    after = len(l2['children'])
                    removed = before != after
                    print(f'删除 L3 孤节点「熏、烧、烤肉类」: {before} -> {after}')
                    break
            break

    # 2. 复制甲基汞通类 row 到 L4 肉食性鱼类
    copied = 0
    target_food = '肉食性鱼类及其制品(金枪鱼、金目鲷、枪鱼及以上鱼类的制品、鲨鱼及以上鱼类的制品除外)'
    target_a1_l4 = '肉食性鱼类（例如：金枪鱼、金目鲷、枪鱼、鲨鱼等）'
    for con in data['contaminants']:
        if con['table_no'] != 3:
            continue
        # 只找甲基汞 pollutant（注意 pollutant 可能带 ' a' 脚注后缀）
        for it in con['items']:
            pollutant = (it.get('pollutant') or '').replace(' a', '').strip()
            if pollutant == '甲基汞' and it.get('food') == target_food and not it.get('a1_l4'):
                # 检查是否已存在复制
                exists = any(x.get('food') == target_food and x.get('a1_l4') == target_a1_l4 for x in con['items'])
                if exists:
                    print('复制 row 已存在，跳过')
                    break
                new_it = {**it, 'a1_l4': target_a1_l4}
                # 保持原顺序：在原 row 后插入
                idx = con['items'].index(it)
                con['items'].insert(idx + 1, new_it)
                copied += 1
                print(f'复制甲基汞通类 row 到 L4 肉食性鱼类: food={target_food}, limit={it.get("limit_value")}')
                break

    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'完成: 删除孤节点={removed}, 复制 row={copied}')


if __name__ == '__main__':
    main()
