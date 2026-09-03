"""v82-fix95: T2 Cd 畜禽肝脏/肾脏 row 复制挂 L3 畜禽内脏

- T2 镉 畜禽肝脏及其制品 0.5 (原挂 L2 肉类, 复制挂 L3 畜禽内脏)
- T2 镉 畜禽肾脏及其制品 1.0 (原挂 L2 肉类, 复制挂 L3 畜禽内脏)
- a1_l3 字段: '' → '畜禽内脏（例如：肝、肾、肺、肠等）'
- a1_l4 保持 '' (A.1 树 L3 畜禽内脏下无 L4 子节点)
- 风格: v82-fix89 wood/silver 多节点复制
"""
import json
import shutil

JSON_FILE = 'data/gb2762/gb2762_2025.json'
BAK = JSON_FILE + '.bak.v82fix95_meat_offal_l3'

L3_NAME = '畜禽内脏（例如：肝、肾、肺、肠等）'

def main():
    shutil.copy(JSON_FILE, BAK)
    print(f'备份 → {BAK}')

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    found_count = 0
    for ci, c in enumerate(data['contaminants']):
        if c['table_no'] != 2:
            continue
        for ri, row in enumerate(c['items']):
            food = row.get('food', '')
            if (food in ['畜禽肝脏及其制品', '畜禽肾脏及其制品']
                    and row.get('a1_l1') == '肉及肉制品'
                    and row.get('a1_l2') == '肉类（生鲜肉、冷却肉、冷冻肉等）'
                    and row.get('a1_l3') == ''
                    and row.get('a1_l4') == ''):
                # 复制 row
                new_row = dict(row)
                new_row['a1_l3'] = L3_NAME
                new_row['a1_l4'] = ''
                # 在 ri+1 位置插入
                c['items'].insert(ri + 1, new_row)
                found_count += 1
                print(f'  ✓ T2 镉 {food} {row["limit_value"]} 复制挂 L3 畜禽内脏')
                # 跳过刚插入的 row，继续下一个原 row
                continue

    if found_count == 0:
        print('未找到目标 row')
        return

    print(f'\n共复制挂载 {found_count} 条 row')

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'✓ {JSON_FILE} 更新完成')

if __name__ == '__main__':
    main()
