"""v82-fix87 修复 OCR 错误合并的除外项

原数据:
- Pb 表 1 食用菌: '...、木耳、银耳及以上食用菌的制品除外'
- Cd 表 2 食用菌: '...、木耳、银耳及以上食用菌的制品除外'
- Hg 表 3 肉食性鱼类: '...、枪鱼、鲨鱼及以上鱼类的制品除外'

按 PDF 原文 + OCR 解析, 「木耳」「银耳及以上食用菌的制品」「枪鱼」
「鲨鱼及以上鱼类的制品」 应当是独立 excl 项, 但 OCR 解析中被合并。

修复: 把 '木耳、银耳及以上食用菌的制品' 拆成 '木耳及以上食用菌的制品、
银耳及以上食用菌的制品', 让 isApplicableToPath split('及以上') 后启用
substring 匹配, 正确排除 '木耳制品' / '银耳制品' L4 节点。

同理: '枪鱼、鲨鱼及以上鱼类的制品' → '枪鱼及以上鱼类的制品、鲨鱼及以上鱼类的制品'
"""
import json, os, shutil

DATA = 'data/gb2762/gb2762_2025.json'
BAK = 'data/gb2762/gb2762_2025.json.bak.v82fix87_split_excl'
if not os.path.exists(BAK):
    shutil.copy2(DATA, BAK)

with open(DATA,'r',encoding='utf-8') as f:
    d = json.load(f)

fixed = 0
for c in d['contaminants']:
    for it in c['items']:
        food = it.get('food','')
        new_food = food
        new_food = new_food.replace('木耳、银耳及以上食用菌的制品', '木耳及以上食用菌的制品、银耳及以上食用菌的制品')
        new_food = new_food.replace('枪鱼、鲨鱼及以上鱼类的制品', '枪鱼及以上鱼类的制品、鲨鱼及以上鱼类的制品')
        if new_food != food:
            it['food'] = new_food
            fixed += 1

with open(DATA,'w',encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print(f'修复 {fixed} 条 row food 字段')
