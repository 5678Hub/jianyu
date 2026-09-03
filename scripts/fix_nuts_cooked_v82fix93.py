"""v82-fix93: L3「熟制坚果及籽类（带壳、脱壳、包衣）」复挂 2 条 row

触发
- 用户：「熟制坚果及籽类（带壳、脱壳、包衣）加两类」
- T1 铅 生咖啡豆及烘焙咖啡豆 0.5 (现挂 L2 生干坚果)
- T2 镉 花生 0.5 (现挂 L2 生干坚果)
- 用户方案 B: 复制挂 L3「熟制坚果及籽类（带壳、脱壳、包衣）」

修复
- T1 铅插 idx+1: 复制生咖啡豆 + 改 a1_l3='熟制坚果及籽类（带壳、脱壳、包衣）', a1_l4=''
- T2 镉插 idx+1: 复制花生 + 改 a1_l3='熟制坚果及籽类（带壳、脱壳、包衣）', a1_l4=''
"""
import json
import shutil

SRC = 'data/gb2762/gb2762_2025.json'
BACKUP = 'data/gb2762/gb2762_2025.json.bak.v82fix93_nuts_cooked'

L3_NAME = '熟制坚果及籽类（带壳、脱壳、包衣）'

def main():
    shutil.copy(SRC, BACKUP)
    print(f'备份 → {BACKUP}')

    with open(SRC, 'r', encoding='utf-8') as f:
        data = json.load(f)

    targets = [
        (0, '生咖啡豆及烘焙咖啡豆'),  # T1 铅
        (1, '花生'),                   # T2 镉
    ]

    for ci, food_name in targets:
        cont = data['contaminants'][ci]
        # 找源 row 位置
        src_idx = None
        for ri, row in enumerate(cont['items']):
            if row.get('food') == food_name:
                src_idx = ri
                break
        if src_idx is None:
            print(f'  ⚠️  ci={ci} T{cont["table_no"]} 未找到 food={food_name}')
            continue

        src_row = cont['items'][src_idx]
        # 复制
        new_row = dict(src_row)
        new_row['a1_l3'] = L3_NAME
        new_row['a1_l4'] = ''
        # 在 src_idx + 1 位置插入
        cont['items'].insert(src_idx + 1, new_row)
        print(f'  ✓ T{cont["table_no"]} {cont["contaminant"]} 复挂: {food_name!r} → L3 {L3_NAME}')

    # 写回
    with open(SRC, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 写 _last_fix
    data['_last_fix'] = 'v82-fix93-nuts-cooked-duplicate-2026-09-03'
    with open(SRC, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n✓ {SRC} 更新完成')

if __name__ == '__main__':
    main()
