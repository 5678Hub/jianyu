"""v82-fix96: 删 L2 肉类中 Cd 畜禽肝脏/肾脏 2 条 row

- 用户反馈：「L2肉类中删掉：T2 镉 Cd 畜禽肝脏及其制品 0.5 mg/kg / T2 镉 Cd 畜禽肾脏及其制品 1.0 mg/kg」
- 现状：L2 肉类 idx 命中 6 条 row（含这 2 条 ri=49/51，a1_l3=''，由 v82-fix91 撤 a1_l4 后 fallback B 挂到 L2 肉类）
- 保留：v82-fix95 复制的 ri=50/52 已挂 L3 畜禽内脏
- 删除：ri=49/51 (a1_l3='' 的原始 row)
- 修改后:
  - L2 肉类 idx: 6 → 4 条（删 2 条 Cd 肝/肾）
  - L3 畜禽内脏 idx: 3 条不变（ri=47 Pb 0.5 + ri=50 Cd 肝 + ri=52 Cd 肾）
"""
import json
import shutil

JSON_FILE = 'data/gb2762/gb2762_2025.json'
BAK = JSON_FILE + '.bak.v82fix96_meat_l2_remove'

def main():
    shutil.copy(JSON_FILE, BAK)
    print(f'备份 → {BAK}')

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    removed = []
    for ci, c in enumerate(data['contaminants']):
        if c['table_no'] != 2:
            continue
        # 倒序遍历，避免删除时索引错位
        for ri in range(len(c['items']) - 1, -1, -1):
            row = c['items'][ri]
            food = row.get('food', '')
            if (food in ['畜禽肝脏及其制品', '畜禽肾脏及其制品']
                    and row.get('a1_l1') == '肉及肉制品'
                    and row.get('a1_l2') == '肉类（生鲜肉、冷却肉、冷冻肉等）'
                    and row.get('a1_l3') == ''
                    and row.get('a1_l4') == ''):
                removed.append((ci, ri, food, row['limit_value']))
                del c['items'][ri]

    print(f'删除了 {len(removed)} 条 row:')
    for ci, ri, food, lim in removed:
        print(f'  ci={ci} 原 ri={ri} T2 镉 {food} {lim}')

    if not removed:
        print('未找到目标 row')
        return

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n✓ {JSON_FILE} 更新完成')

if __name__ == '__main__':
    main()
