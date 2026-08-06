"""生成 subcategory_ids.json（master.json 的 114 个细类 → 稳定英文 slug ID）"""
import json
import os
import json

# 手动简繁 + 拼音映射
MANUAL_SLUGS = {
    '其他方便食品': 'other_convenient_food',
    '其他水产制品': 'other_aquatic_products_processed',
    '干制水产品': 'dried_aquatic_products',
    '其他水产品': 'other_aquatic_products',
    '海水虾': 'sea_shrimp',
    '海水鱼': 'marine_fish',
    '淡水虾': 'freshwater_shrimp',
    '淡水鱼': 'freshwater_fish',
    '蜜饯': 'candied_fruit',
    '柑、橘': 'mandarin_orange',
    '柑橘': 'citrus',
    '桑葚': 'mulberry',
    '梨': 'pear',
    '水果类': 'fruits_placeholder',
    '番木瓜': 'papaya',
    '芒果': 'mango',
    '荔枝': 'lychee',
    '菠萝': 'pineapple',
    '香蕉': 'banana',
    '龙眼': 'longan',
    '淀粉': 'starch',
    '粉丝粉条': 'vermicelli',
    '炒货食品及坚果制品': 'roasted_seeds_nuts',
    '花生制品': 'peanut_products',
    '营养补充品': 'nutritional_supplement',
    '生干坚果与籽类食品': 'raw_dried_seeds_nuts',
    '其他畜肉': 'other_livestock_meat',
    '牛肉': 'beef',
    '猪肝': 'pork_liver',
    '羊肉': 'mutton',
    '鸡肉': 'chicken',
    '其他谷物粉类制成品': 'other_cereal_powder_products',
    '发酵面制品': 'fermented_dough_products',
    '挂面': 'dried_noodles',
    '生湿面制品': 'fresh_noodle_products',
    '月饼': 'mooncake',
    '糕点': 'pastries',
    '果冻': 'jelly',
    '果脯蜜饯': 'preserved_fruit',
    '糖果': 'candy',
    '水果罐头': 'canned_fruit',
    '其他肉制品': 'other_meat_products',
    '熏煮香肠火腿制品': 'smoked_sausage_ham',
    '熟肉制品': 'cooked_meat',
    '腌腊肉制品': 'cured_meat',
    '酱卤肉制品': 'sauced_meat',
    '茶叶': 'tea',
    '其他类蔬菜': 'other_vegetables',
    '姜': 'ginger',
    '山药': 'yam',
    '普通白菜（小白菜、小油菜、青菜）': 'bok_choy',
    '甘薯': 'sweet_potato',
    '甜椒': 'sweet_pepper',
    '胡萝卜': 'carrot',
    '芹菜': 'celery',
    '茄子': 'eggplant',
    '菜豆': 'string_bean',
    '菠菜': 'spinach',
    '萝卜': 'radish',
    '葱': 'green_onion',
    '蔬菜': 'vegetables_placeholder',
    '豆芽': 'bean_sprouts',
    '豇豆': 'cowpea',
    '辣椒': 'chili_pepper',
    '韭菜': 'leek',
    '食荚豌豆': 'snow_pea',
    '马铃薯': 'potato',
    '黄瓜': 'cucumber',
    '蔬菜干制品': 'dried_vegetable_products',
    '酱腌菜': 'pickled_vegetables',
    '薯类和膨化食品': 'puffed_food',
    '蜂产品': 'bee_products',
    '蜂蜜': 'honey',
    '其他香辛料调味品': 'other_spice_seasonings',
    '普通食用盐': 'edible_salt',
    '辣椒、花椒、辣椒粉、花椒粉': 'chili_pepper_sichuan_pepper_powder',
    '酱油': 'soy_sauce',
    '酿造酱': 'brewed_paste',
    '食醋': 'vinegar',
    '香辛料调味油': 'spice_seasoning_oil',
    '其他豆制品': 'other_soy_products',
    '豆制品': 'soy_products_placeholder',
    '非发酵性豆制品': 'non_fermented_soy_products',
    '其他豆类': 'other_beans',
    '速冻动物性水产制品': 'frozen_animal_aquatic_products',
    '速冻肉制品': 'frozen_meat_products',
    '速冻面米食品': 'frozen_dough_rice_food',
    '以蒸馏酒及食用酒精为酒基的配制酒': 'distilled_alcohol_based_blended_liquor',
    '啤酒': 'beer',
    '果酒': 'fruit_wine',
    '白酒': 'baijiu',
    '葡萄酒': 'grape_wine',
    '酒类': 'alcoholic_beverages_placeholder',
    '黄酒': 'huangjiu',
    '芝麻油': 'sesame_oil',
    '食用植物油': 'edible_vegetable_oil',
    '其他餐饮食品': 'other_restaurant_food',
    '复用餐饮具（餐馆自行消毒）': 'reused_tableware_restaurant_disinfected',
    '油饼油条（自制）': 'fried_dough_sticks_self_made',
    '生食动物性水产制品(自制)': 'raw_animal_aquatic_products_self_made',
    '粉丝粉条（自制）': 'vermicelli_self_made',
    '自制油炸面制品': 'self_made_fried_dough_products',
    '除上述类别的餐饮加工自制食品': 'other_restaurant_self_made_food',
    '馒头花卷（自制）': 'steamed_bun_self_made',
    '其他饮料': 'other_beverages',
    '包装饮用水': 'packaged_drinking_water',
    '果蔬汁': 'fruit_vegetable_juice',
    '果蔬汁类及其饮料': 'fruit_vegetable_juice_beverages',
    '碳酸饮料': 'carbonated_beverages',
    '饮用天然矿泉水': 'natural_mineral_water',
    '饮用纯净水': 'purified_water',
    '饼干': 'biscuits',
    '鸡蛋': 'chicken_eggs',
    '冷冻饮品': 'frozen_drinks_placeholder',
}


EXTENDED_SLUGS = {
    # GB 检验项目表里出现但 master 没有的细类（简繁 + 拼音）
    # 粮食加工品
    '小麦粉': 'wheat_flour',
    '大米': 'rice',
    '其他粮食加工品': 'other_cereal_products',
    '玉米粉': 'corn_flour',
    '米粉': 'rice_noodles',
    '其他谷物粉类制成品': 'other_cereal_powder_products',
    '谷物碾磨加工品': 'cereal_milling_products',
    # 食用油、油脂及其制品
    '食用植物油': 'edible_vegetable_oil',
    '食用动物油': 'edible_animal_oil',
    '油脂制品': 'oil_fat_products',
    # 调味品
    '酱油': 'soy_sauce',
    '食醋': 'vinegar',
    '酱类': 'paste',
    '调味料酒': 'cooking_wine',
    '香辛料类': 'spices',
    '香辛料调味品': 'spice_seasonings',
    '其他调味品': 'other_seasonings',
    '水产调味品': 'aquatic_seasonings',
    # 肉制品
    '预制肉制品': 'prepared_meat_products',
    '调理肉制品': 'prepared_meat',
    '腌腊肉制品': 'cured_meat',
    '熟肉制品': 'cooked_meat',
    '其他肉制品': 'other_meat_products',
    '熏烧烤肉制品': 'smoked_roasted_meat',
    '肉灌肠类': 'meat_sausage',
    # 乳制品
    '液体乳': 'liquid_milk',
    '乳粉': 'milk_powder',
    '其他乳制品': 'other_dairy_products',
    '婴幼儿配方乳粉': 'infant_formula_milk_powder',
    '较大婴儿和幼儿配方乳粉': 'older_infant_formula_milk_powder',
    '特殊医学用途婴儿配方食品': 'fsmp_infant_formula',
    '其他特殊膳食食品': 'other_special_dietary_food',
    '孕妇及乳母营养补充食品': 'pregnant_lactating_supplement',
    # 饮料
    '包装饮用水': 'packaged_drinking_water',
    '果蔬汁类及其饮料': 'fruit_vegetable_juice_beverages',
    '碳酸饮料': 'carbonated_beverages',
    '茶饮料': 'tea_beverages',
    '咖啡饮料': 'coffee_beverages',
    '植物蛋白饮料': 'plant_protein_beverages',
    '其他饮料': 'other_beverages',
    '固体饮料': 'solid_beverages',
    # 方便食品
    '方便面': 'instant_noodles',
    '其他方便食品': 'other_convenient_food',
    '方便粥': 'instant_porridge',
    '方便米饭': 'instant_rice',
    '其他方便米面制品': 'other_instant_rice_noodle_products',
    '调味面制品': 'seasoned_dough_products',
    # 饼干
    '饼干': 'biscuits',
    '其他饼干': 'other_biscuits',
    # 罐头
    '畜禽肉罐头': 'meat_canned',
    '水产品罐头': 'aquatic_canned',
    '蔬菜罐头': 'vegetable_canned',
    '水果罐头': 'canned_fruit',
    '其他罐头': 'other_canned_food',
    # 冷冻饮品
    '冰淇淋': 'ice_cream',
    '雪糕': 'ice_lolly',
    '冰棍': 'popsicle',
    '食用冰': 'edible_ice',
    '冷冻饮品': 'frozen_drinks_placeholder',
    # 速冻食品
    '速冻面米食品': 'frozen_dough_rice_food',
    '速冻肉制品': 'frozen_meat_products',
    '速冻水产制品': 'frozen_aquatic_products',
    '速冻蔬菜制品': 'frozen_vegetable_products',
    '其他速冻食品': 'other_frozen_food',
    # 薯类和膨化食品
    '薯类食品': 'potato_food',
    '膨化食品': 'puffed_food',
    # 糖果制品
    '糖果': 'candy',
    '巧克力': 'chocolate',
    '代可可脂巧克力': 'cocoa_butter_substitute_chocolate',
    '果冻': 'jelly',
    '其他糖果制品': 'other_confectionery',
    # 茶叶及相关制品
    '茶叶': 'tea',
    '代用茶': 'herbal_tea',
    # 酒类
    '白酒': 'baijiu',
    '葡萄酒': 'grape_wine',
    '啤酒': 'beer',
    '黄酒': 'huangjiu',
    '果酒': 'fruit_wine',
    '其他蒸馏酒': 'other_distilled_liquor',
    '其他发酵酒': 'other_fermented_liquor',
    '配制酒': 'blended_liquor',
    # 蔬菜制品
    '酱腌菜': 'pickled_vegetables',
    '蔬菜干制品': 'dried_vegetable_products',
    '其他蔬菜制品': 'other_vegetable_products',
    # 水果制品
    '蜜饯': 'candied_fruit',
    '果脯': 'preserved_fruit',
    '水果罐头（水果制品）': 'canned_fruit_processed',
    '其他水果制品': 'other_fruit_products',
    # 炒货食品及坚果制品
    '炒货食品': 'roasted_seeds',
    '坚果': 'nuts',
    '其他炒货食品及坚果制品': 'other_roasted_seeds_nuts',
    # 蛋制品
    '再制蛋': 'reconstituted_eggs',
    '干蛋制品': 'dry_egg_products',
    '冰蛋制品': 'frozen_egg_products',
    '液蛋制品': 'liquid_egg_products',
    '热凝固蛋制品': 'heat_coagulated_egg_products',
    '其他蛋制品': 'other_egg_products',
    # 可可及焙烤咖啡产品
    '可可制品': 'cocoa_products',
    '焙烤咖啡豆': 'roasted_coffee_beans',
    '焙烤咖啡粉': 'roasted_coffee_powder',
    # 食糖
    '白砂糖': 'white_sugar',
    '绵白糖': 'soft_white_sugar',
    '赤砂糖': 'brown_sugar',
    '冰糖': 'rock_sugar',
    '其他食糖': 'other_sugar',
    # 水产制品
    '干制水产品': 'dried_aquatic_products',
    '盐渍水产品': 'salted_aquatic_products',
    '鱼糜制品': 'surimi_products',
    '冷冻鱼糜制品': 'frozen_surimi_products',
    '其他水产制品': 'other_aquatic_products_processed',
    # 淀粉及淀粉制品
    '淀粉': 'starch',
    '淀粉制品': 'starch_products_placeholder',
    '粉丝粉条': 'vermicelli',
    '其他淀粉制品': 'other_starch_products',
    # 糕点
    '糕点': 'pastries',
    '月饼': 'mooncake',
    '其他糕点': 'other_pastries',
    # 豆制品
    '非发酵性豆制品': 'non_fermented_soy_products',
    '发酵性豆制品': 'fermented_soy_products',
    '其他豆制品': 'other_soy_products',
    '豆制品': 'soy_products_placeholder',
    # 蜂产品
    '蜂蜜': 'honey',
    '蜂王浆': 'royal_jelly',
    '蜂花粉': 'bee_pollen',
    '其他蜂产品': 'other_bee_products',
    '蜂产品': 'bee_products',
    # 保健食品
    '保健食品': 'health_food',
    # 特殊膳食食品
    '婴幼儿谷类辅助食品': 'infant_cereal_assist_food',
    '辅食营养补充品': 'complementary_food_supplement',
    '运动营养食品': 'sports_nutrition_food',
    '其他特殊膳食食品': 'other_special_dietary_food_placeholder',
    '营养补充品': 'nutritional_supplement',
    # 餐饮食品
    '餐饮具': 'tableware',
    '复用餐饮具（餐馆自行消毒）': 'reused_tableware_restaurant_disinfected',
    '复用餐饮具（集中清洗消毒服务单位提供）': 'reused_tableware_central_disinfected',
    '油饼油条（自制）': 'fried_dough_sticks_self_made',
    '生食动物性水产制品(自制)': 'raw_animal_aquatic_products_self_made',
    '粉丝粉条（自制）': 'vermicelli_self_made',
    '自制油炸面制品': 'self_made_fried_dough_products',
    '馒头花卷（自制）': 'steamed_bun_self_made',
    '其他餐饮食品': 'other_restaurant_food',
    '除上述类别的餐饮加工自制食品': 'other_restaurant_self_made_food',
    # 食用农产品
    '畜禽肉': 'livestock_meat',
    '其他畜肉': 'other_livestock_meat',
    '禽肉': 'poultry',
    '其他禽肉': 'other_poultry',
    '畜副产品': 'livestock_offal',
    '禽副产品': 'poultry_offal',
    '其他畜禽副产品': 'other_livestock_poultry_offal',
    '猪肉': 'pork',
    '牛肉': 'beef',
    '羊肉': 'mutton',
    '禽副产品（鸡）': 'poultry_offal_chicken',
    '猪肝': 'pork_liver',
    '鸡蛋': 'chicken_eggs',
    '鸭蛋': 'duck_eggs',
    '其他蛋': 'other_eggs',
    '海水鱼': 'marine_fish',
    '海水虾': 'sea_shrimp',
    '海水蟹': 'sea_crab',
    '海水贝': 'sea_shellfish',
    '淡水鱼': 'freshwater_fish',
    '淡水虾': 'freshwater_shrimp',
    '淡水蟹': 'freshwater_crab',
    '其他水产品': 'other_aquatic_products',
    '贝类': 'shellfish',
    '柑橘': 'citrus',
    '柑、橘': 'mandarin_orange',
    '梨': 'pear',
    '芒果': 'mango',
    '荔枝': 'lychee',
    '香蕉': 'banana',
    '龙眼': 'longan',
    '菠萝': 'pineapple',
    '番木瓜': 'papaya',
    '桑葚': 'mulberry',
    '其他水果': 'other_fruits',
    '蔬菜': 'vegetables_placeholder',
    '豆类': 'beans_placeholder',
    '其他豆类': 'other_beans',
    '姜': 'ginger',
    '山药': 'yam',
    '普通白菜（小白菜、小油菜、青菜）': 'bok_choy',
    '甘薯': 'sweet_potato',
    '甜椒': 'sweet_pepper',
    '胡萝卜': 'carrot',
    '芹菜': 'celery',
    '茄子': 'eggplant',
    '菜豆': 'string_bean',
    '菠菜': 'spinach',
    '萝卜': 'radish',
    '葱': 'green_onion',
    '豆芽': 'bean_sprouts',
    '豇豆': 'cowpea',
    '辣椒': 'chili_pepper',
    '韭菜': 'leek',
    '食荚豌豆': 'snow_pea',
    '马铃薯': 'potato',
    '黄瓜': 'cucumber',
    '其他类蔬菜': 'other_vegetables',
    '禽肉（鸡肉）': 'poultry_chicken',
    '鸡肉': 'chicken',
    '生干坚果与籽类食品': 'raw_dried_seeds_nuts',
    '花生制品': 'peanut_products',
    '酒类': 'alcoholic_beverages_placeholder',
    '果冻（糖果制品）': 'jelly_confectionery',
    '果脯蜜饯': 'preserved_fruit_candied',
    '水产品（生食）': 'aquatic_raw',
    '水产品（鲜活）': 'aquatic_fresh',
    '粉丝粉条(自制)': 'vermicelli_self_made_alt',
    '以蒸馏酒及食用酒精为酒基的配制酒': 'distilled_alcohol_based_blended_liquor',
    '熟肉干制品': 'cooked_dried_meat',
    '调味面制品(自制)': 'seasoned_dough_self_made',
    '坚果与籽类食品': 'nuts_seeds_food',
    '其他坚果与籽类食品': 'other_nuts_seeds',
    '酱卤肉制品': 'sauced_meat',
    '熏煮香肠火腿制品': 'smoked_sausage_ham',
    '果蔬汁': 'fruit_vegetable_juice',
    '饮用天然矿泉水': 'natural_mineral_water',
    '饮用纯净水': 'purified_water',
    '其他香辛料调味品': 'other_spice_seasonings',
    '普通食用盐': 'edible_salt',
    '辣椒、花椒、辣椒粉、花椒粉': 'chili_pepper_sichuan_pepper_powder',
    '酿造酱': 'brewed_paste',
    '香辛料调味油': 'spice_seasoning_oil',
    '速冻动物性水产制品': 'frozen_animal_aquatic_products',
}


# 合并
MANUAL_SLUGS.update(EXTENDED_SLUGS)


def auto_slug(name):
    """自动生成英文 slug：去括号/标点 → 拼音 → snake_case → 保留 ASCII 词"""
    import re
    import pypinyin
    # 去括号内容（含括号）+ 中文标点
    s = re.sub(r'[（(][^）)]*[）)]', '', name)
    s = re.sub(r'[、，,。:：]', ' ', s)
    s = s.strip()
    if not s:
        return 'unknown'
    # 拼音转换
    pys = pypinyin.lazy_pinyin(s, style=pypinyin.NORMAL)
    slug = '_'.join(p for p in pys if p).lower()
    slug = re.sub(r'[^a-z0-9_]', '_', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug or 'unknown'


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    m = json.load(open(os.path.join(root, 'data/master.json'), encoding='utf-8'))
    gc = json.load(open(os.path.join(root, 'data/current_period/gb_checklist_subcat.json'), encoding='utf-8'))
    ids = json.load(open(os.path.join(root, 'data/category_ids.json'), encoding='utf-8'))
    by_name = ids['by_name']

    # 收集 master.json 的 (big, sub_name)
    pairs_master = sorted(set(
        (r['big_category'],
         r['sub_category'].split('-', 1)[1] if '-' in r['sub_category'] else r['sub_category'])
        for r in m['records'] if r.get('sub_category')
    ))

    # 收集 gb_checklist_subcat.json 的 (big, sub_name)
    pairs_gb = []
    for big, subs in gc.get('categories', {}).items():
        for s in subs:
            if isinstance(s, dict):
                pairs_gb.append((big, s['name']))

    # 合并去重（master 优先）
    sub_list = []
    seen_sub = set()
    missing = []

    def add_entry(big, sub_name, source):
        big_id = by_name.get(big)
        if not big_id:
            missing.append(f'{big}|||{sub_name} (big 未映射)')
            return
        if sub_name in MANUAL_SLUGS:
            sub_slug = MANUAL_SLUGS[sub_name]
            slug_kind = 'manual'
        else:
            sub_slug = auto_slug(sub_name)
            slug_kind = 'auto'
            # 仅当 auto 失败时记 missing
            if not sub_slug or sub_slug == 'unknown':
                missing.append(f'{big}|||{sub_name} (slug 生成失败)')
                return
        full_id = f'{big_id}-{sub_slug}'
        if full_id not in seen_sub:
            seen_sub.add(full_id)
            sub_list.append({
                'id': full_id,
                'big_category_id': big_id,
                'big_category_name': big,
                'name': sub_name,
                'source': source,
                'slug_kind': slug_kind,
            })

    for big, sub_name in pairs_master:
        add_entry(big, sub_name, 'master')
    for big, sub_name in pairs_gb:
        add_entry(big, sub_name, 'gb_checklist')

    print(f'生成 {len(sub_list)} 条 subcategory_id')
    if missing:
        print(f'⚠️ {len(missing)} 条未映射（仅展示前 20）：')
        for m_ in missing[:20]:
            print(f'  {m_}')

    # 写 subcategory_ids.json
    out = {
        '_meta': {
            'schema_version': '1.0',
            'last_updated': '2026-08-06 10:10:00+08:00',
            'description': 'jianyu 全部细类（master + GB 检验项目表）→ 稳定英文 slug ID；manual = 人工指定；auto = pypinyin 生成',
            'count': len(sub_list),
            'sources': {
                'master': sum(1 for s in sub_list if s['source'] == 'master'),
                'gb_checklist': sum(1 for s in sub_list if s['source'] == 'gb_checklist'),
            },
            'slug_kinds': {
                'manual': sum(1 for s in sub_list if s['slug_kind'] == 'manual'),
                'auto': sum(1 for s in sub_list if s['slug_kind'] == 'auto'),
            },
        },
        'subcategories': sub_list,
        'by_big_sub': {
            f'{s["big_category_name"]}|||{s["name"]}': s['id'] for s in sub_list
        },
    }
    out_path = os.path.join(root, 'data/subcategory_ids.json')
    open(out_path, 'w', encoding='utf-8').write(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print(f'✅ data/subcategory_ids.json 写入 {len(sub_list)} 条')


if __name__ == '__main__':
    main()