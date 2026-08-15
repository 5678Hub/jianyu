#!/usr/bin/env python3
"""
重写表 9 苯并[a]芘为用户精确给出的 11 行;
清空表 5 锡(用户自行填写);
不动其他表。
"""
import json
from copy import deepcopy

JSON_PATH = "data/gb2762/gb2762_2025.json"


# 表 9 苯并[a]芘 — 按用户截图 11 行精确写入
TABLE9_ITEMS = [
    # 谷物·2.0 μg/kg(展开为 7 行)
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物",
        "a1_l3": "稻谷",
        "a1_l4": "",
    },
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物碾磨加工品",
        "a1_l3": "糙米(包括色稻米)",
        "a1_l4": "",
    },
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物碾磨加工品",
        "a1_l3": "大米(粉)",
        "a1_l4": "",
    },
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物",
        "a1_l3": "小麦",
        "a1_l4": "",
    },
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物碾磨加工品",
        "a1_l3": "小麦粉(包括食用麸皮)",
        "a1_l4": "",
    },
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物",
        "a1_l3": "玉米",
        "a1_l4": "",
    },
    {
        "category": "谷物及其制品",
        "food": "稻谷、糙米、大米(粉)、小麦、小麦粉、玉米、玉米粉、玉米糁(渣)",
        "limit": "2.0",
        "remark": "a",
        "a1_l1": "谷物及其制品(不包括焙烤制品)",
        "a1_l2": "谷物碾磨加工品",
        "a1_l3": "玉米粉、玉米糁(渣)",
        "a1_l4": "",
    },
    # 熏、烧、烤肉类·5.0 μg/kg
    {
        "category": "肉及肉制品",
        "food": "熏、烧、烤肉类",
        "limit": "5.0",
        "remark": "",
        "a1_l1": "肉及肉制品",
        "a1_l2": "肉制品(包括内脏制品、血制品)",
        "a1_l3": "熟肉制品",
        "a1_l4": "熏、烧、烤肉类",
    },
    # 熏、烤水产品·5.0 μg/kg
    {
        "category": "水产动物及其制品",
        "food": "熏、烤水产品",
        "limit": "5.0",
        "remark": "",
        "a1_l1": "水产动物及其制品",
        "a1_l2": "水产制品",
        "a1_l3": "熏、烤水产品",
        "a1_l4": "",
    },
    # 稀奶油、奶油、无水奶油·10 μg/kg
    {
        "category": "乳及乳制品",
        "food": "稀奶油、奶油、无水奶油",
        "limit": "10",
        "remark": "",
        "a1_l1": "乳及乳制品",
        "a1_l2": "稀奶油、奶油、无水奶油",
        "a1_l3": "",
        "a1_l4": "",
    },
    # 油脂及其制品·10 μg/kg
    {
        "category": "油脂及其制品",
        "food": "油脂及其制品",
        "limit": "10",
        "remark": "",
        "a1_l1": "油脂及其制品",
        "a1_l2": "",
        "a1_l3": "",
        "a1_l4": "",
    },
]


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for tab in data["contaminants"]:
        if tab.get("table_no") == 9:
            tab["items"] = TABLE9_ITEMS
            print(f"✅ 表 9 已重写为 {len(TABLE9_ITEMS)} 行")
        elif tab.get("table_no") == 5:
            tab["items"] = []
            print(f"✅ 表 5 已清空(待用户填写)")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已写回 {JSON_PATH}")


if __name__ == "__main__":
    main()