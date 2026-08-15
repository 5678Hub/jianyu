#!/usr/bin/env python3
"""
全面扫描重写 A.1 4 级分类:
- 对每条 item,根据 food 字段在 A.1 树中找所有命中的 L2/L3/L4 节点
- 每个命中叶节点展开为独立行,共享原 item 的 food/limit/unit/footnote/sub_label/sub_limit
- 表 3/4/8 双列字段(sub_label/sub_limit)完整保留
- 写回 JSON,再生成最终 Excel
"""
import json
import re
from copy import deepcopy


JSON_PATH = "data/gb2762/gb2762_2025.json"
TMP_PATH = "data/gb2762/_gb2762_2025_食品类别_v6.xlsx"


def normalize(s):
    if not s:
        return ""
    return (
        s.replace("（", "(")
        .replace("）", ")")
        .replace("：", ":")
        .replace("，", ",")
        .replace("；", ";")
        .replace(" ", "")
        .replace("\u3000", "")
    )


def short_name(s):
    if not s:
        return ""
    n = normalize(s)
    for sep in ["(", "（"]:
        idx = n.find(sep)
        if idx > 0:
            return n[:idx]
    return n


def extract_keywords(name):
    if not name:
        return set()
    n = normalize(name)
    keywords = set()
    cleaned = n
    while "(" in cleaned:
        s = cleaned.find("(")
        e = cleaned.find(")", s)
        if e == -1:
            break
        inner = cleaned[s + 1 : e]
        for kw in re.split(r"[,、:]", inner):
            kw = kw.strip().rstrip("等")
            for prefix in ["例如", "如", "比如", "例如:", "如:"]:
                if kw.startswith(prefix):
                    kw = kw[len(prefix) :]
                    kw = kw.strip()
            if 2 <= len(kw) <= 10:
                keywords.add(kw)
        cleaned = cleaned[:s] + cleaned[e + 1 :]
    keywords.add(short_name(name))
    for kw in re.split(r"[,、]", cleaned):
        kw = kw.strip().rstrip("等")
        if 2 <= len(kw) <= 10:
            keywords.add(kw)
    return keywords - {""}


def name_variants(name):
    """生成节点名的所有匹配变体"""
    return ({normalize(name), short_name(name)} | extract_keywords(name)) - {""}


# L2/L3 短名后跟的"模糊后缀",出现时不算独立命中
# 例如"调制乳"+"粉" → "调制乳粉" 不算 "调制乳"
AMBIGUOUS_SUFFIXES = "粉类品制品罐头干汁酱油菜鱼肉蛋糖奶酒"


def node_appears_in(node, food_norm):
    """
    检查节点的某个变体是否在 food_norm 中作为**独立短语**出现。
    排除"调制乳"被"调制乳粉"误命中这类情况。
    """
    for v in name_variants(node["name"]):
        if not v or len(v) < 2:
            continue
        pos = 0
        while True:
            idx = food_norm.find(v, pos)
            if idx == -1:
                break
            end = idx + len(v)
            next_char = food_norm[end] if end < len(food_norm) else ""
            # 排除模糊后缀:如"调制乳"+"粉" 不算独立命中
            if next_char and next_char in AMBIGUOUS_SUFFIXES:
                pos = end
                continue
            # 前置字符也不能是汉字(避免子串部分匹配,如"豆类"+"制品"里的子串)
            prev_char = food_norm[idx - 1] if idx > 0 else ""
            # 前置字符若是汉字且不是分隔符(、,，()《》),则视为更长词的一部分,不命中
            if prev_char and prev_char not in "、,，()（）《》 \t":
                pos = end
                continue
            return True
    return False


def find_l1_node(tree, l1_name):
    """通过短名匹配。短名是 node.name 的前 N 个字符(去除括号后缀)。
    支持 L1 节点带括号描述(如"蔬菜及其制品(包括薯类,不包括食用菌)")"""
    if not l1_name:
        return None
    needle = short_name(l1_name)
    for n in tree:
        if short_name(n["name"]) == needle:
            return n
    return None


def infer_L1_from_food(food, tree):
    """从 food 字段推断 L1 节点(关键词命中,优先详细后粗略)"""
    if not food:
        return None
    f = normalize(food)
    KEYWORDS = [
        ("婴幼儿", "特殊膳食用食品"),
        ("特殊医学用途", "特殊膳食用食品"),
        ("辅食营养", "特殊膳食用食品"),
        ("运动营养", "特殊膳食用食品"),
        ("孕妇及乳母", "特殊膳食用食品"),
        ("食品", "食品"),
        ("冷冻饮品", "冷冻饮品"),
        ("可可制品", "可可制品、巧克力和巧克力制品以及糖果"),
        ("巧克力", "可可制品、巧克力和巧克力制品以及糖果"),
        ("糖果", "可可制品、巧克力和巧克力制品以及糖果"),
        ("焙烤食品", "焙烤食品"),
        ("面包", "焙烤食品"),
        ("糕点", "焙烤食品"),
        ("饼干", "焙烤食品"),
        ("食用淀粉", "淀粉及淀粉制品(包括谷物、豆类和块根植物提取的淀粉)"),
        ("淀粉制品", "淀粉及淀粉制品(包括谷物、豆类和块根植物提取的淀粉)"),
        ("食糖及淀粉糖", "食糖及淀粉糖"),
        ("食糖", "食糖及淀粉糖"),
        ("酒类", "酒类"),
        ("白酒", "酒类"),
        ("黄酒", "酒类"),
        ("葡萄酒", "酒类"),
        ("饮料", "饮料类"),
        ("饮用天然矿泉水", "饮料类"),
        ("饮用纯净水", "饮料类"),
        ("葡萄汁", "饮料类"),
        ("包装饮用水", "饮料类"),
        ("果蔬汁", "饮料类"),
        ("含乳饮料", "饮料类"),
        ("固体饮料", "饮料类"),
        ("蛋白饮料", "饮料类"),
        ("碳酸饮料", "饮料类"),
        ("茶饮料", "饮料类"),
        ("调味品", "调味品"),
        ("食用盐", "调味品"),
        ("味精", "调味品"),
        ("酱油", "调味品"),
        ("食醋", "调味品"),
        ("香辛料", "调味品"),
        ("水产调味品", "调味品"),
        ("鱼类调味品", "调味品"),
        ("复合调味料", "调味品"),
        ("油脂", "油脂及其制品"),
        ("植物油", "油脂及其制品"),
        ("动物油", "油脂及其制品"),
        ("鱼油", "油脂及其制品"),
        ("氢化植物油", "油脂及其制品"),
        ("磷虾油", "油脂及其制品"),
        ("蛋及蛋制品", "蛋及蛋制品"),
        ("鲜蛋", "蛋及蛋制品"),
        ("生乳", "乳及乳制品"),
        ("巴氏杀菌乳", "乳及乳制品"),
        ("灭菌乳", "乳及乳制品"),
        ("调制乳", "乳及乳制品"),
        ("发酵乳", "乳及乳制品"),
        ("乳粉", "乳及乳制品"),
        ("干酪", "乳及乳制品"),
        ("稀奶油", "乳及乳制品"),
        ("乳及乳制品", "乳及乳制品"),
        ("鲜、冻水产动物", "水产动物及其制品"),
        ("鱼类", "水产动物及其制品"),
        ("甲壳类", "水产动物及其制品"),
        ("双壳贝类", "水产动物及其制品"),
        ("海蜇", "水产动物及其制品"),
        ("金枪鱼", "水产动物及其制品"),
        ("金目鲷", "水产动物及其制品"),
        ("枪鱼", "水产动物及其制品"),
        ("鲨鱼", "水产动物及其制品"),
        ("水产制品", "水产动物及其制品"),
        ("干制水产品", "水产动物及其制品"),
        ("海蟹", "水产动物及其制品"),
        ("虾蛄", "水产动物及其制品"),
        ("水产动物", "水产动物及其制品"),
        ("畜禽肝脏", "肉及肉制品"),
        ("畜禽肾脏", "肉及肉制品"),
        ("畜禽内脏", "肉及肉制品"),
        ("肉制品", "肉及肉制品"),
        ("肉类", "肉及肉制品"),
        ("肉及肉制品", "肉及肉制品"),
        ("坚果及籽类", "坚果及籽类"),
        ("花生", "坚果及籽类"),
        ("生咖啡豆", "坚果及籽类"),
        ("藻类", "藻类及其制品"),
        ("螺旋藻", "藻类及其制品"),
        ("食用菌", "食用菌及其制品"),
        ("香菇", "食用菌及其制品"),
        ("木耳", "食用菌及其制品"),
        ("银耳", "食用菌及其制品"),
        ("松茸", "食用菌及其制品"),
        ("牛肝菌", "食用菌及其制品"),
        # 新鲜蔬菜/水果/蔬菜制品 优先于豆类(防"豆类蔬菜"误命中"豆类")
        ("新鲜蔬菜", "蔬菜及其制品"),
        ("蔬菜制品", "蔬菜及其制品"),
        ("酱腌菜", "蔬菜及其制品"),
        ("干制蔬菜", "蔬菜及其制品"),
        ("芹菜", "蔬菜及其制品"),
        ("黄花菜", "蔬菜及其制品"),
        ("蔬菜", "蔬菜及其制品"),
        ("蔓越莓", "水果及其制品"),
        ("醋栗", "水果及其制品"),
        ("新鲜水果", "水果及其制品"),
        ("果酱", "水果及其制品"),
        ("蜜饯", "水果及其制品"),
        ("水果", "水果及其制品"),
        ("豆类", "豆类及其制品"),
        ("豆浆", "豆类及其制品"),
        ("豆腐", "豆类及其制品"),
        ("谷物", "谷物及其制品(不包括焙烤制品)"),
        ("麦片", "谷物及其制品(不包括焙烤制品)"),
        ("面筋", "谷物及其制品(不包括焙烤制品)"),
        ("稻谷", "谷物及其制品(不包括焙烤制品)"),
        ("糙米", "谷物及其制品(不包括焙烤制品)"),
        ("大米", "谷物及其制品(不包括焙烤制品)"),
        ("小麦", "谷物及其制品(不包括焙烤制品)"),
        ("玉米", "谷物及其制品(不包括焙烤制品)"),
        ("茶叶", "其他类(除上述食品以外的食品)"),
        ("干菊花", "其他类(除上述食品以外的食品)"),
        ("苦丁茶", "其他类(除上述食品以外的食品)"),
        ("蜂蜜", "其他类(除上述食品以外的食品)"),
        ("花粉", "其他类(除上述食品以外的食品)"),
        ("果冻", "其他类(除上述食品以外的食品)"),
        ("膨化食品", "其他类(除上述食品以外的食品)"),
        ("食用燕窝", "其他类(除上述食品以外的食品)"),
    ]
    for kw, l1_name in KEYWORDS:
        if kw in f:
            node = find_l1_node(tree, l1_name)
            if node:
                return node
    return None


def match_in_tree(item, l1_node):
    """
    在 l1_node 下递归找所有匹配的 L2/L3/L4 路径。
    返回: list of (l2_name, l3_name, l4_name)
    """
    food = item.get("food", "") or ""
    food_norm = normalize(food)

    results = []

    # 整类条目(以"除外"结尾)→ L1 only,不入此函数
    if food.endswith("除外") or food.endswith("等除外") or "、除外" in food:
        return results

    # 优先:精确 deep match
    # 先看哪些 L2 显式出现
    l2_candidates = []
    for l2 in l1_node.get("children", []):
        if node_appears_in(l2, food_norm):
            l2_candidates.append(l2)

    # 扩展:如果 L2 名称没命中,但其 L3/L4 子节点有命中,也算 L2 命中
    if not l2_candidates:
        for l2 in l1_node.get("children", []):
            for l3 in l2.get("children", []):
                if node_appears_in(l3, food_norm):
                    l2_candidates.append(l2)
                    break
                for l4 in l3.get("children", []):
                    if node_appears_in(l4, food_norm):
                        l2_candidates.append(l2)
                        break
                if l2 in l2_candidates:
                    break

    if not l2_candidates:
        return results  # caller 会 fallback L1 only

    # 对每个候选 L2,看其 L3 子节点是否也有命中
    for l2 in l2_candidates:
        l2_name = l2["name"]
        l3_kids = l2.get("children", [])
        if not l3_kids:
            # 无 L3,只展开 1 行(L2 本身)
            results.append((l2_name, "", ""))
            continue
        # 有 L3,看哪些 L3 显式出现
        matching_l3 = [l3 for l3 in l3_kids if node_appears_in(l3, food_norm)]
        # 也看 L4 是否命中
        matching_l4_first = []
        if not matching_l3:
            for l3 in l3_kids:
                for l4 in l3.get("children", []):
                    if node_appears_in(l4, food_norm):
                        matching_l4_first.append((l3, l4))
        if not matching_l3 and not matching_l4_first:
            # 没显式 L3/L4 命中 → L3 填空,只展开 1 行(L2)
            results.append((l2_name, "", ""))
        elif matching_l4_first:
            # 有 L4 命中(L3 显式没),逐个展开
            for l3, l4 in matching_l4_first:
                results.append((l2_name, l3["name"], l4["name"]))
        else:
            # 有显式 L3 命中,逐个展开
            for l3 in matching_l3:
                l3_name = l3["name"]
                l4_kids = l3.get("children", [])
                if not l4_kids:
                    results.append((l2_name, l3_name, ""))
                else:
                    matching_l4 = [l4 for l4 in l4_kids if node_appears_in(l4, food_norm)]
                    if not matching_l4:
                        for l4 in l4_kids:
                            results.append((l2_name, l3_name, l4["name"]))
                    else:
                        for l4 in matching_l4:
                            results.append((l2_name, l3_name, l4["name"]))
    return results


def expand_item(item, tree):
    """
    展开 item 为多行。每行共享原 food/limit/unit/footnote/sub_*
    返回 list of (L1, L2, L3, L4)
    """
    food = item.get("food", "") or ""

    # 保护:如果 L1/L2/L3/L4 已经有非空精确值,跳过 reduce 重新展开
    # (保护表 5/7/9 等用户已精确填的项)
    existing_L1 = item.get("a1_l1", "") or ""
    existing_L2 = item.get("a1_l2", "") or ""
    existing_L3 = item.get("a1_l3", "") or ""
    existing_L4 = item.get("a1_l4", "") or ""
    if existing_L1:
        # 已有 L1,直接保留 L1/L2/L3/L4
        return [(existing_L1, existing_L2, existing_L3, existing_L4)]

    # 先去掉括号以正确判断"除外"
    food_strip = normalize(food).rstrip(")）)")

    # 整类条目,保持 L1 only 单行
    if food_strip.endswith("除外") or food_strip.endswith("等除外") or "、除外" in food_strip:
        L1 = item.get("category_a1", "") or item.get("category", "")
        L1_node = find_l1_node(tree, L1)
        if not L1_node:
            L1_node = infer_L1_from_food(food, tree)
            if L1_node:
                L1 = L1_node["name"]
        if L1_node:
            return [(L1_node["name"], "", "", "")]
        return [(L1, "", "", "")]

    # 1. 找 L1
    L1 = item.get("category_a1", "") or item.get("category", "")
    L1_node = find_l1_node(tree, L1)
    if not L1_node:
        # 推断 L1
        L1_node = infer_L1_from_food(food, tree)
        if L1_node:
            L1 = L1_node["name"]
        else:
            return [(L1, "", "", "")]

    # 2. 在 L1 节点下找 L2/L3/L4 展开
    matches = match_in_tree(item, L1_node)

    if not matches:
        # fallback L1 only
        return [(L1_node["name"], "", "", "")]

    # 去重:如果多个 L2 互为字符串前缀关系,只保留最长的(最具体的)
    def dedup_specific(matches):
        # 按 L2 字符串长度降序
        sorted_m = sorted(matches, key=lambda m: -len(short_name(m[0])))
        kept = []
        for m in sorted_m:
            sn = short_name(m[0])
            covered = False
            for k in kept:
                ksn = short_name(k[0])
                # 长名覆盖短名
                if ksn.startswith(sn) and len(ksn) > len(sn):
                    covered = True
                    break
            if not covered:
                kept.append(m)
        return kept

    matches = dedup_specific(matches)

    # 去重 tuple
    seen = set()
    out = []
    for l2, l3, l4 in matches:
        key = (L1_node["name"], l2, l3, l4)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def rebuild_json(data):
    """对每条 item 做展开,重写 JSON"""
    tree = data["appendix_a1"]["tree"]
    new_contaminants = []

    for tab in data["contaminants"]:
        new_items = []
        for it in tab["items"]:
            expansions = expand_item(it, tree)
            for L1, L2, L3, L4 in expansions:
                new_it = deepcopy(it)
                new_it["a1_l1"] = L1
                new_it["a1_l2"] = L2
                new_it["a1_l3"] = L3
                new_it["a1_l4"] = L4
                new_items.append(new_it)
        new_tab = deepcopy(tab)
        new_tab["items"] = new_items
        new_contaminants.append(new_tab)

    data["contaminants"] = new_contaminants
    return data


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"加载 {JSON_PATH}")
    data = rebuild_json(data)

    # 统计
    total = sum(len(t["items"]) for t in data["contaminants"])
    print(f"展开后总条目数: {total}")

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已写回 {JSON_PATH}")


if __name__ == "__main__":
    main()
