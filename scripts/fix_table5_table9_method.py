"""修复三件事:
1. A.1 树添加'食品'大类(L1),共 23 个大类
2. 表 5 锡 4 行(全部挂 a 脚注,检验方法 GB 5009.16)
3. 表 9 苯并[a]芘 a 脚注只保留稻谷行
4. 包装饮用水 method 从 GB 5009.12 改成 GB 8538
"""
import json

JSON_PATH = "data/gb2762/gb2762_2025.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# === 1. A.1 树新增'食品'大类 ===
tree = data["appendix_a1"]["tree"]
existing_names = {n["name"] for n in tree}
if "食品" not in existing_names:
    # 插入到末尾,作为新增大类(放在'其他类'之后)
    food_node = {
        "name": "食品",
        "children": [
            {"name": "食品(饮料类、婴幼儿配方食品、婴幼儿辅助食品除外)", "children": []},
            {"name": "饮料类", "children": [{"name": "包装饮用水", "children": []}]},
            {"name": "婴幼儿配方食品", "children": []},
            {"name": "婴幼儿辅助食品", "children": []},
        ],
    }
    tree.append(food_node)
    print(f"✓ A.1 树新增'食品'大类,L1 总数: {len(tree)}")

# === 2. 表 5 锡 4 行 ===
for tab in data["contaminants"]:
    if tab.get("table_no") == 5:
        # 删旧,写新
        tab["items"] = [
            {
                "category": "食品",
                "food": "食品(饮料类、婴幼儿配方食品、婴幼儿辅助食品除外)",
                "limit": "250 mg/kg",
                "limit_value": "250",
                "a1_l1": "食品",
                "a1_l2": "食品(饮料类、婴幼儿配方食品、婴幼儿辅助食品除外)",
                "a1_l3": "",
                "a1_l4": "",
                "remark": "a",
                "inspection_method": "GB 5009.16",
                "test_method": "食品按 GB 5009.16 规定的方法测定。",
            },
            {
                "category": "食品",
                "food": "饮料类",
                "limit": "150 mg/kg",
                "limit_value": "150",
                "a1_l1": "食品",
                "a1_l2": "饮料类",
                "a1_l3": "",
                "a1_l4": "",
                "remark": "a",
                "inspection_method": "GB 5009.16",
                "test_method": "食品按 GB 5009.16 规定的方法测定。",
            },
            {
                "category": "食品",
                "food": "婴幼儿配方食品",
                "limit": "50 mg/kg",
                "limit_value": "50",
                "a1_l1": "食品",
                "a1_l2": "婴幼儿配方食品",
                "a1_l3": "",
                "a1_l4": "",
                "remark": "a",
                "inspection_method": "GB 5009.16",
                "test_method": "食品按 GB 5009.16 规定的方法测定。",
            },
            {
                "category": "食品",
                "food": "婴幼儿辅助食品",
                "limit": "50 mg/kg",
                "limit_value": "50",
                "a1_l1": "食品",
                "a1_l2": "婴幼儿辅助食品",
                "a1_l3": "",
                "a1_l4": "",
                "remark": "a",
                "inspection_method": "GB 5009.16",
                "test_method": "食品按 GB 5009.16 规定的方法测定。",
            },
        ]
        # 表 5 表级脚注 a 完整文本
        if "footnotes" not in tab:
            tab["footnotes"] = []
        # 确保 a 脚注完整文本存在
        has_a = any(f.get("label") == "a" for f in tab.get("footnotes", []))
        if not has_a:
            tab.setdefault("footnotes", []).append({
                "label": "a",
                "text": "仅限于采用镀锡薄钢板容器包装的食品。"
            })
        print(f"✓ 表 5 锡:写入 4 行,全部挂 a 脚注")
        break

# === 3. 表 9 苯并[a]芘 a 脚注只保留稻谷行 ===
for tab in data["contaminants"]:
    if tab.get("table_no") == 9:
        for it in tab["items"]:
            l3 = it.get("a1_l3", "") or ""
            # 只在 L3=稻谷 时保留 a,其他去掉
            if l3 == "稻谷":
                it["remark"] = "a"
            else:
                it["remark"] = ""
        print(f"✓ 表 9 苯并[a]芘:a 脚注仅保留稻谷行")
        break

# === 4. 包装饮用水 method 改 GB 8538 ===
# 规则:在 items 中,如果 a1_l1/a1_l2/a1_l3/a1_l4/food 任意含"包装饮用水"且不是"除外"描述
# 且 method 含 GB 5009.12,则 method 改 GB 8538
replaced = 0
for tab in data["contaminants"]:
    # 先扫 tab 级 inspection_method
    for it in tab["items"]:
        l1 = it.get("a1_l1", "") or ""
        l2 = it.get("a1_l2", "") or ""
        l3 = it.get("a1_l3", "") or ""
        l4 = it.get("a1_l4", "") or ""
        food = it.get("food", "") or ""

        # 只在精确指向"包装饮用水" 时替换(不是"除外"列表中的提及)
        is_pure_water = (
            "包装饮用水" in l2 or "包装饮用水" in l3 or "包装饮用水" in l4
        ) and "除外" not in food
        if not is_pure_water:
            continue

        # 改 method:包装饮用水统一用 GB 8538
        it["inspection_method"] = "GB 8538"
        # test_method 给完整句子,优先保留原句风格
        it["test_method"] = "包装饮用水按 GB 8538 规定的方法测定。"
        replaced += 1

# 也扫 tab 级 inspection_method_rules
for tab in data["contaminants"]:
    rules = tab.get("inspection_method_rules", []) or []
    for rule in rules:
        old = rule.get("method", "") or ""
        if "GB 5009.12" in old and "包装饮用水" in (rule.get("food_match", "") or ""):
            rule["method"] = old.replace("GB 5009.12", "GB 8538")

print(f"✓ 包装饮用水 method 替换完成,共 {replaced} 行")

# 写回
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n已保存 JSON")