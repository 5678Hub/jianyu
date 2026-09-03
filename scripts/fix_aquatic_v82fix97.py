"""v82-fix97: 水产动物及其制品章节数据校对

按用户 2026-09-03 13:42 确认方案 A（PDF 原文严格展示）：
- L3 软体动物 own 段空（PDF 主表无通类 row）
- L4 双壳贝类/腹足类/头足类 各挂对应 row
- L3 棘皮类 挂对应 row
- L4 肉食性鱼类 挂金枪鱼/金目鲷/枪鱼/鲨鱼 Hg/甲基汞 row
- (坚果及籽类 L3 熟制坚果复挂是特殊情况，不参考)

具体改动：
1. T1 Pb 双壳贝类 1.5 (ri=23) a1_l4='双壳贝类' (不再挂 L3 软体动物)
2. T2 Cd 双壳贝类、腹足类、头足类、棘皮类 2.0 (ri=56/57/58 冗余):
   - ri=56 a1_l4='双壳贝类' food='双壳贝类'
   - ri=57 a1_l4='腹足类' food='腹足类'
   - ri=58 a1_l4='头足类' food='头足类'
   - 新增 1 条 a1_l3='棘皮类' food='棘皮类'
3. T3 Hg 金枪鱼/金目鲷/枪鱼/鲨鱼 移挂 L4 肉食性鱼类
4. T3 甲基汞 金枪鱼/金目鲷/枪鱼/鲨鱼 移挂 L4 肉食性鱼类
"""
import json
import shutil

JSON_FILE = 'data/gb2762/gb2762_2025.json'
BAK = JSON_FILE + '.bak.v82fix97_aquatic'

L4_PREDATOR = '肉食性鱼类（例如：金枪鱼、金目鲷、枪鱼、鲨鱼等）'

def main():
    shutil.copy(JSON_FILE, BAK)
    print(f'备份 → {BAK}')

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # ========== 改动 1: T1 Pb 双壳贝类 1.5 → 移挂 L4 双壳贝类 ==========
    moved_pb = 0
    for ci, c in enumerate(data['contaminants']):
        if c['table_no'] != 1:
            continue
        for row in c['items'][:]:
            if (row.get('food') == '双壳贝类'
                    and row.get('a1_l1') == '水产动物及其制品'
                    and row.get('a1_l2') == '鲜、冻水产动物'
                    and row.get('a1_l3') == '软体动物'
                    and row.get('a1_l4') == ''):
                row['a1_l4'] = '双壳贝类'
                moved_pb += 1
                print(f'  ✓ T1 Pb 双壳贝类 1.5 a1_l4=双壳贝类')
                break

    # ========== 改动 2: T2 Cd 软体动物 3 条冗余 → 拆 4 挂 ==========
    modified_cd = 0
    for c in data['contaminants']:
        if c['table_no'] != 2:
            continue
        target_l4 = ['双壳贝类', '腹足类', '头足类']
        matched = []
        for ri, row in enumerate(c['items']):
            if (row.get('food') == '双壳贝类、腹足类、头足类、棘皮类'
                    and row.get('a1_l1') == '水产动物及其制品'
                    and row.get('a1_l3') == '软体动物'
                    and row.get('a1_l4') == ''):
                matched.append((ri, row))
        if len(matched) >= 3:
            # 前 3 条分别挂 3 个 L4
            for (ri, row), l4_name in zip(matched[:3], target_l4):
                row['a1_l4'] = l4_name
                row['food'] = l4_name
                modified_cd += 1
                print(f'  ✓ T2 Cd {l4_name} 2.0 a1_l4={l4_name}')
            # 第 4 条 (任意一条) 复制挂 L3 棘皮类
            src_row = matched[0][1]
            new_row = dict(src_row)
            new_row['a1_l3'] = '棘皮类'
            new_row['a1_l4'] = ''
            new_row['food'] = '棘皮类'
            c['items'].append(new_row)
            modified_cd += 1
            print(f'  ✓ T2 Cd 棘皮类 2.0 a1_l3=棘皮类 (新增)')

    # ========== 改动 3: T3 Hg/甲基汞 4 种鱼 → 移挂 L4 肉食性鱼类 ==========
    moved_predator = 0
    predator_names = ['金枪鱼', '金目鲷', '枪鱼', '鲨鱼']
    for c in data['contaminants']:
        if c['table_no'] != 3:
            continue
        for row in c['items'][:]:
            food = row.get('food', '')
            if '肉食性鱼类及其制品' in food:
                continue  # 排除通类
            for name in predator_names:
                if food == f'{name}及其制品' and row.get('a1_l1') == '水产动物及其制品':
                    row['a1_l2'] = '鲜、冻水产动物'
                    row['a1_l3'] = '鱼类'
                    row['a1_l4'] = L4_PREDATOR
                    moved_predator += 1
                    print(f'  ✓ T3 {row["pollutant"]} {food} {row["limit_value"]} 移挂 L4 肉食性鱼类')
                    break

    print(f'\n汇总:')
    print(f'  T1 Pb 双壳贝类 移挂: {moved_pb} 条')
    print(f'  T2 Cd 软体动物拆挂: {modified_cd} 条')
    print(f'  T3 Hg/甲基汞 4 鱼移挂: {moved_predator} 条')

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n✓ {JSON_FILE} 更新完成')

if __name__ == '__main__':
    main()
