#!/usr/bin/env python3
"""
补全 JSON 表 3/4/8 的双列限量值(总汞/甲基汞 a、总砷/无机砷 a、亚硝酸盐/硝酸盐)
"""
import json

JSON_PATH = "data/gb2762/gb2762_2025.json"

# 表 3 汞完整数据(总汞 / 甲基汞 a)
TABLE3_DATA = [
    # (food, 总汞, 甲基汞 a, 脚注)
    ("水产动物及其制品、肉食性鱼类及其制品除外", "—", "0.5", ""),
    ("肉食性鱼类及其制品(金枪鱼、金目鲷、枪鱼、鲨鱼及以上鱼类的制品除外)", "—", "1.0", ""),
    ("金枪鱼及其制品", "—", "1.2", ""),
    ("金目鲷及其制品", "—", "1.5", ""),
    ("枪鱼及其制品", "—", "1.7", ""),
    ("鲨鱼及其制品", "—", "1.6", ""),
    ("稻谷b、糙米、大米(粉)、玉米、玉米粉、玉米糁(渣)、小麦、小麦粉", "0.02", "—", "b"),
    ("新鲜蔬菜", "0.01", "—", ""),
    ("食用菌及其制品、木耳及其制品、银耳及其制品除外", "—", "0.1", ""),
    ("木耳及其制品、银耳及其制品(干重计)", "—", "0.1", ""),  # 干重计
    ("肉类", "0.05", "—", ""),
    ("生乳、巴氏杀菌乳、灭菌乳、调制乳、发酵乳", "0.01", "—", ""),
    ("鲜蛋", "0.05", "—", ""),
    ("食用盐", "0.1", "—", ""),
    ("饮用天然矿泉水", "0.001mg/L", "—", ""),
    ("婴幼儿罐装辅助食品", "0.02", "—", ""),
]

# 表 8 亚硝酸盐/硝酸盐 双列补充(在原 JSON 基础上添加硝酸盐列)
# 数据格式: (food, 亚硝酸盐, 硝酸盐, 脚注)
TABLE8_DATA = [
    ("酱腌菜", "20", "—", ""),
    ("生乳", "0.4", "—", ""),
    ("乳粉和调制乳粉", "2.0", "—", ""),
    ("包装饮用水(饮用天然矿泉水除外)", "0.1", "—", "以NO2-计"),
    ("饮用天然矿泉水", "0.1mg/L", "45mg/L", "亚硝酸盐以NO2-计,硝酸盐以NO3-计"),
    ("婴儿配方食品、较大婴儿配方食品、幼儿配方食品", "2.0", "100", "a,b,c(以固态产品计)"),
    ("特殊医学用途婴儿配方食品", "2.0", "100", "以固态产品计"),
    ("婴幼儿谷类辅助食品", "2.0", "100", "d,c"),
    ("婴幼儿罐装辅助食品", "4.0", "200", "d,c"),
    ("特殊医学用途配方食品(特殊医学用途婴儿配方食品涉及的品种除外)", "2.0", "100", "e,c(以固态产品计)"),
    ("辅食营养补充品", "2.0", "100", "b,c"),
    ("孕妇及乳母营养补充食品", "2.0", "100", "d,c"),
    ("食用燕窝", "30", "—", ""),
]


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # === 表 3 汞:替换为完整 16 行 ===
    for tab in data["contaminants"]:
        if tab["table_no"] != 3:
            continue
        # 找到表 3 的索引
        tab3_idx = data["contaminants"].index(tab)
        # 构建新的 items
        new_items = []
        for food, total_hg, methyl_hg, footnote in TABLE3_DATA:
            new_items.append(
                {
                    "category": "水产动物及其制品" if "水产" in food
                                else "谷物及其制品" if "稻谷" in food or "糙米" in food
                                else "蔬菜及其制品" if "蔬菜" in food
                                else "食用菌及其制品" if "食用菌" in food or "木耳" in food or "银耳" in food
                                else "肉及肉制品" if food == "肉类"
                                else "乳及乳制品" if "乳" in food
                                else "蛋及蛋制品" if "鲜蛋" in food
                                else "调味品" if "食用盐" in food
                                else "饮料类" if "矿泉水" in food
                                else "特殊膳食用食品" if "婴幼儿" in food
                                else "",
                    "category_a1": "水产动物及其制品" if "水产" in food
                                   else "谷物及其制品(不包括焙烤制品)" if "稻谷" in food or "糙米" in food
                                   else "蔬菜及其制品(包括薯类,不包括食用菌)" if "蔬菜" in food
                                   else "食用菌及其制品" if "食用菌" in food or "木耳" in food or "银耳" in food
                                   else "肉及肉制品" if food == "肉类"
                                   else "乳及乳制品" if "乳" in food
                                   else "蛋及蛋制品" if "鲜蛋" in food
                                   else "调味品" if "食用盐" in food
                                   else "饮料类" if "矿泉水" in food
                                   else "婴幼儿辅助食品" if "婴幼儿" in food
                                   else "",
                    "food": food,
                    "limit": total_hg,  # 总汞值(主列)
                    "sub_limit": methyl_hg,  # 甲基汞 a 值
                    "sub_label": "甲基汞 a",
                    "remark": footnote,
                    "limits": [
                        {"label": "总汞(以 Hg 计)", "value": total_hg},
                        {"label": "甲基汞 a(以 Hg 计)", "value": methyl_hg},
                    ],
                    "subcategories": [],
                    "category_matched_by": "",
                }
            )
        tab["items"] = new_items
        # 更新检验方法
        tab["inspection_method"] = "饮用天然矿泉水按 GB 8538 规定的方法测定,其他食品按 GB 5009.17 规定的方法测定。"
        # 更新污染物名称为"总汞"(主),"甲基汞 a"(子)
        tab["contaminant"] = "总汞"
        tab["full_name"] = "汞(总汞 + 甲基汞 a)"
        tab["sub_pollutants"] = [
            {"name": "总汞", "symbol": "Hg", "value_col": "limit"},
            {"name": "甲基汞 a", "symbol": "Hg", "value_col": "sub_limit"},
        ]
        print(f"表 3 已重写为 {len(new_items)} 行(含甲基汞 a)")

    # === 表 4 砷:补全无机砷 a 列(在现有 items 上添加 sub_limit) ===
    # 当前 JSON 表 4 已有 31 条,但都只有单列。需要补全无机砷 a 列
    # 基于 PDF:
    # 总砷 / 无机砷 a
    # PDF 表 4 数据(主要):
    # 谷物(稻谷除外) - 0.5 / —
    # 稻谷 - — / 0.35 (b)
    # 谷物碾磨加工品(糙米、大米(粉)除外) - 0.5 / —
    # 糙米 - — / 0.35
    # 大米(粉) - — / 0.2
    # 水产动物及其制品(鱼类及其制品除外) - — / 0.5
    # 鱼类及其制品 - — / 0.1
    # 新鲜蔬菜 - 0.5 / —
    # 食用菌及其制品(松茸、木耳、银耳除外) - — / 0.5
    # 松茸及其制品 - — / 0.8
    # 木耳、银耳(干重计) - — / 0.5
    # 肉及肉制品 - 0.5 / —
    # ...

    TABLE4_DATA = {
        "谷物(稻谷除外)": ("0.5", "—", ""),
        "稻谷": ("—", "0.35", "b"),
        "谷物碾磨加工品(糙米、大米(粉)除外)": ("0.5", "—", ""),
        "糙米": ("—", "0.35", ""),
        "大米(粉)": ("—", "0.2", ""),
        "水产动物及其制品(鱼类及其制品除外)": ("—", "0.5", ""),
        "鱼类及其制品": ("—", "0.1", ""),
        "新鲜蔬菜": ("0.5", "—", ""),
        "食用菌及其制品(松茸及其制品、木耳及其制品、银耳及其制品除外)": ("—", "0.5", ""),
        "松茸及其制品": ("—", "0.8", ""),
        "木耳及其制品、银耳及其制品(干重计)": ("—", "0.5", ""),
        "肉及肉制品": ("0.5", "—", ""),
        "生乳、巴氏杀菌乳、灭菌乳、调制乳、发酵乳": ("0.1", "—", ""),
        "乳粉和调制乳粉": ("0.5", "—", ""),
        "油脂及其制品(鱼油及其制品、磷虾油及其制品除外)": ("0.1", "—", ""),
        "鱼油及其制品、磷虾油及其制品": ("—", "0.1", ""),
        "调味品(水产调味品、复合调味料和香辛料类除外)": ("0.5", "—", ""),
        "水产调味品(鱼类调味品除外)": ("—", "0.5", ""),
        "鱼类调味品": ("—", "0.1", ""),
        "复合调味料": ("—", "0.1", ""),
        "食糖及淀粉糖": ("0.5", "—", ""),
        "包装饮用水": ("0.01mg/L", "—", ""),
        "可可制品、巧克力和巧克力制品": ("0.5", "—", ""),
        "婴幼儿谷类辅助食品(添加藻类的产品除外)": ("—", "0.2", ""),
        "添加藻类的产品": ("—", "0.3", ""),
        "婴幼儿罐装辅助食品(以水产及动物肝脏为原料的产品除外)": ("—", "0.1", ""),
        "以水产及动物肝脏为原料的产品": ("—", "0.3", ""),
        "辅食营养补充品": ("0.5", "—", ""),
        "运动营养食品(固态、半固态或粉状)": ("0.5", "—", ""),
        "运动营养食品(液态)": ("0.2", "—", ""),
        "孕妇及乳母营养补充食品": ("0.5", "—", ""),
    }

    for tab in data["contaminants"]:
        if tab["table_no"] != 4:
            continue
        # 现有 items 的 limit 是无机砷 a 值(因为 PDF 大多数是无机砷 a)
        # 需要重新组织:total_as (总砷) 和 inorganic_as (无机砷 a)
        new_items = []
        for food, (total_as, inorg_as, footnote) in TABLE4_DATA.items():
            new_items.append(
                {
                    "category": "谷物及其制品" if "谷物" in food or "稻谷" in food or "糙米" in food
                                else "水产动物及其制品" if "水产" in food or "鱼类" in food
                                else "蔬菜及其制品" if "蔬菜" in food
                                else "食用菌及其制品" if "食用菌" in food or "松茸" in food or "木耳" in food
                                else "肉及肉制品" if "肉" in food
                                else "乳及乳制品" if "乳" in food
                                else "油脂及其制品" if "油脂" in food or "鱼油" in food or "磷虾油" in food
                                else "调味品" if "调味" in food
                                else "食糖及淀粉糖" if "食糖" in food
                                else "饮料类" if "包装饮用水" in food
                                else "可可制品、巧克力和巧克力制品以及糖果" if "可可" in food
                                else "婴幼儿辅助食品" if "婴幼儿" in food
                                else "特殊膳食用食品" if "辅食" in food or "运动" in food or "孕妇" in food
                                else "",
                    "category_a1": "谷物及其制品(不包括焙烤制品)" if "谷物" in food or "稻谷" in food or "糙米" in food
                                   else "水产动物及其制品" if "水产" in food or "鱼类" in food
                                   else "蔬菜及其制品(包括薯类,不包括食用菌)" if "蔬菜" in food
                                   else "食用菌及其制品" if "食用菌" in food or "松茸" in food or "木耳" in food
                                   else "肉及肉制品" if "肉" in food
                                   else "乳及乳制品" if "乳" in food
                                   else "油脂及其制品" if "油脂" in food or "鱼油" in food or "磷虾油" in food
                                   else "调味品" if "调味" in food
                                   else "食糖及淀粉糖" if "食糖" in food
                                   else "饮料类" if "包装饮用水" in food
                                   else "可可制品、巧克力和巧克力制品以及糖果" if "可可" in food
                                   else "婴幼儿辅助食品" if "婴幼儿" in food
                                   else "特殊膳食用食品" if "辅食" in food or "运动" in food or "孕妇" in food
                                   else "",
                    "food": food,
                    "limit": total_as,  # 总砷
                    "sub_limit": inorg_as,  # 无机砷 a
                    "sub_label": "无机砷 a",
                    "remark": footnote,
                    "limits": [
                        {"label": "总砷(以 As 计)", "value": total_as},
                        {"label": "无机砷 a(以 As 计)", "value": inorg_as},
                    ],
                    "subcategories": [],
                    "category_matched_by": "",
                }
            )
        tab["items"] = new_items
        tab["contaminant"] = "总砷"
        tab["full_name"] = "砷(总砷 + 无机砷 a)"
        tab["sub_pollutants"] = [
            {"name": "总砷", "symbol": "As", "value_col": "limit"},
            {"name": "无机砞 a", "symbol": "As", "value_col": "sub_limit"},
        ]
        # 修正检验方法
        tab["inspection_method"] = "按 GB 5009.11 规定的方法测定。"
        print(f"表 4 已重写为 {len(new_items)} 行(含无机砷 a)")

    # === 表 8 亚硝酸盐/硝酸盐:重写为完整双列 ===
    for tab in data["contaminants"]:
        if tab["table_no"] != 8:
            continue
        new_items = []
        for food, no2, no3, footnote in TABLE8_DATA:
            new_items.append(
                {
                    "category": "蔬菜及其制品" if "酱腌菜" in food
                                else "乳及乳制品" if "乳" in food and "婴幼儿" not in food and "辅食" not in food
                                else "饮料类" if "包装饮用水" in food or "矿泉水" in food
                                else "婴幼儿配方食品" if "婴儿配方" in food and "特殊" not in food
                                else "特殊医学用途配方食品" if "特殊医学用途" in food
                                else "婴幼儿辅助食品" if "婴幼儿谷类辅助食品" in food or "婴幼儿罐装辅助食品" in food
                                else "特殊膳食用食品" if "辅食" in food or "孕妇" in food
                                else "其他类(除上述食品以外的食品)" if "燕窝" in food
                                else "",
                    "category_a1": "蔬菜及其制品(包括薯类,不包括食用菌)" if "酱腌菜" in food
                                   else "乳及乳制品" if "乳" in food and "婴幼儿" not in food and "辅食" not in food
                                   else "饮料类" if "包装饮用水" in food or "矿泉水" in food
                                   else "婴幼儿配方食品" if "婴儿配方" in food and "特殊" not in food
                                   else "特殊医学用途配方食品(含特殊医学用途婴儿配方食品)" if "特殊医学用途" in food
                                   else "婴幼儿辅助食品" if "婴幼儿谷类辅助食品" in food or "婴幼儿罐装辅助食品" in food
                                   else "特殊膳食用食品" if "辅食" in food or "孕妇" in food
                                   else "其他类(除上述食品以外的食品)" if "燕窝" in food
                                   else "",
                    "food": food,
                    "limit": no2,  # 亚硝酸盐
                    "sub_limit": no3,  # 硝酸盐
                    "sub_label": "硝酸盐",
                    "remark": footnote,
                    "limits": [
                        {"label": "亚硝酸盐(以 NaNO2 计)", "value": no2},
                        {"label": "硝酸盐(以 NaNO3 计)", "value": no3},
                    ],
                    "subcategories": [],
                    "category_matched_by": "",
                }
            )
        tab["items"] = new_items
        tab["contaminant"] = "亚硝酸盐"
        tab["full_name"] = "亚硝酸盐(NaNO2) + 硝酸盐(NaNO3)"
        tab["sub_pollutants"] = [
            {"name": "亚硝酸盐", "symbol": "NaNO2", "value_col": "limit"},
            {"name": "硝酸盐", "symbol": "NaNO3", "value_col": "sub_limit"},
        ]
        tab["inspection_method"] = "饮料类按 GB 8538 规定的方法测定,其他食品按 GB 5009.33 规定的方法测定。"
        print(f"表 8 已重写为 {len(new_items)} 行(亚硝酸盐 + 硝酸盐)")

    # 写回
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已写回 {JSON_PATH}")


if __name__ == "__main__":
    main()