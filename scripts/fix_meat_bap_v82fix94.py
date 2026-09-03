"""v82-fix94: T9 BaP 熏烧烤 row 移挂 L4

- T9 苯并[a]芘 熏、烧、烤肉类 5.0
- 原 a1: L1 肉及肉制品 → L2 肉制品 → a1_l3='' → a1_l4=熏烧烤
  → walkExact Fallback B 注册到 L3 熏烧烤（肉制品下孤节点，错了）
- 修正 a1_l3: '' → '熟肉制品'
- 新 a1: L1 → L2 肉制品 → L3 熟肉制品 → L4 熏、烧、烤肉类
  → 注册到正确的 L4 节点
"""
import json
import shutil

JSON_FILE = 'data/gb2762/gb2762_2025.json'
BAK = JSON_FILE + '.bak.v82fix94_meat_bap_l4'

def main():
    shutil.copy(JSON_FILE, BAK)
    print(f'备份 → {BAK}')

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    found = False
    for ci, c in enumerate(data['contaminants']):
        if c['table_no'] != 9:
            continue
        for ri, row in enumerate(c['items']):
            if (row.get('food') == '熏、烧、烤肉类'
                    and row.get('a1_l1') == '肉及肉制品'
                    and row.get('a1_l3') == ''
                    and row.get('a1_l4') == '熏、烧、烤肉类'):
                print(f'修改前: T9 ci={ci} ri={ri}')
                print(f'  a1: l1={row["a1_l1"]!r} l2={row["a1_l2"]!r} l3={row["a1_l3"]!r} l4={row["a1_l4"]!r}')
                row['a1_l3'] = '熟肉制品'
                print(f'修改后:')
                print(f'  a1: l1={row["a1_l1"]!r} l2={row["a1_l2"]!r} l3={row["a1_l3"]!r} l4={row["a1_l4"]!r}')
                found = True
                break

    if not found:
        print('未找到目标 row')
        return

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'✓ {JSON_FILE} 更新完成')

if __name__ == '__main__':
    main()
