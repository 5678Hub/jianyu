# -*- coding: utf-8 -*-
"""
GB 2762-2025 JSON 数据层修正（执行版）。
严格按 inspect 实测结果做 14 处定向修改，每项带断言，命中不符即中止。
不改 A.1 树结构（仅 repoint 数据行的 a1 字段）。
"""
import json, sys

P = r"c:\Users\10487\WorkBuddy\jianyu\data\gb2762\gb2762_2025.json"
data = json.load(open(P, encoding="utf-8"))
cont = data["contaminants"]

def tbl(n):
    for c in cont:
        if str(c.get("table_no")) == str(n):
            return c
    raise SystemExit(f"[FATAL] table {n} not found")

def find(c, pred):
    return [it for it in c["items"] if pred(it)]

def assert_eq(actual, expected, msg):
    if actual != expected:
        raise SystemExit(f"[FATAL] {msg}\n   expected={expected!r}\n   actual  ={actual!r}")

log = []
def L(s):
    log.append(s); print(s)

# ---------- 1. 表1 生咖啡豆 note='d' 清空 ----------
c1 = tbl(1)
coffee = find(c1, lambda it: it.get("food") == "生咖啡豆及烘焙咖啡豆" and it.get("note") == "d")
assert_eq(len(coffee), 2, "表1 生咖啡豆 note='d' 行数应为2")
for it in coffee:
    it["note"] = ""
L(f"1. 表1 清 生咖啡豆 note='d' ×{len(coffee)} 行")

# ---------- 2. 表2 花生 note='b' 清空 ----------
c2 = tbl(2)
peanut = find(c2, lambda it: it.get("food") == "花生" and it.get("note") == "b")
assert_eq(len(peanut), 2, "表2 花生 note='b' 行数应为2")
for it in peanut:
    it["note"] = ""
L(f"2. 表2 清 花生 note='b' ×{len(peanut)} 行")

# ---------- 3. 表1 footnotes 删 label='d' ----------
before = len(c1["footnotes"])
c1["footnotes"] = [f for f in c1["footnotes"] if f.get("label") != "d"]
removed = before - len(c1["footnotes"])
assert_eq(removed, 1, "表1 footnotes 应恰好删1条 d")
L(f"3. 表1 footnotes 删 label='d' (剩 {len(c1['footnotes'])} 条)")

# ---------- 4. 表2 footnotes 删 label='b' ----------
before = len(c2["footnotes"])
c2["footnotes"] = [f for f in c2["footnotes"] if f.get("label") != "b"]
removed = before - len(c2["footnotes"])
assert_eq(removed, 1, "表2 footnotes 应恰好删1条 b")
L(f"4. 表2 footnotes 删 label='b' (剩 {len(c2['footnotes'])} 条)")

# ---------- 5. 表8 脚注 e 措辞对齐 PDF ----------
c8 = tbl(8)
e_notes = [f for f in c8["footnotes"] if f.get("label") == "e"]
assert_eq(len(e_notes), 1, "表8 脚注 e 应存在1条")
e_notes[0]["text"] = "仅适用于乳基产品(不含豆类成分)。"
L(f"5. 表8 脚注 e 改为 {e_notes[0]['text']!r}")

# ---------- 6. 表2 inspection_method_rules 加 包装饮用水→GB8538 ----------
cur = c2["inspection_method_rules"]
assert_eq(cur[0].get("is_default"), True, "表2 原规则首条应为 default（全食品→GB5009.15）")
cur.insert(0, {"apply": "包装饮用水", "method": "按 GB 8538 规定的方法测定"})
assert_eq(cur[0]["apply"], "包装饮用水", "新规则应置于首位")
c2["inspection_method"] = "包装饮用水按 GB 8538 规定的方法测定,其他食品按 GB 5009.15 规定的方法测定。"
L(f"6. 表2 rules 加 包装饮用水→GB8538（现 {len(cur)} 条）；表级句同步")

# ---------- 7. 表1 螺旋藻 limit 0.5→2.0(干重计) ----------
spir = find(c1, lambda it: it.get("food") == "螺旋藻")
assert_eq(len(spir), 1, "表1 螺旋藻 行数应为1")
assert_eq(spir[0]["limit_value"], "0.5(干重计)", "表1 螺旋藻 当前值应为 0.5(干重计)")
spir[0]["limit_value"] = "2.0(干重计)"
L(f"7. 表1 螺旋藻 limit 0.5(干重计)→2.0(干重计)")

# ---------- 8. 命名对齐 牛肝菌 (表2) ----------
boletus = find(c2, lambda it: it.get("food") == "松茸、牛肝菌、鸡枞、多汁乳菇及以上食用菌的制品" and it.get("a1_l3") == "牛肝菌")
assert_eq(len(boletus), 1, "表2 牛肝菌 行数应为1")
boletus[0]["a1_l3"] = "牛肝菌[美味牛肝菌,兰茂牛肝菌,茶褐新生牛肝菌,远东邹盖牛肝菌]"
L(f"8. 表2 牛肝菌 a1_l3 对齐")

# ---------- 9. 命名对齐 甲壳类 (表2) 2 行 ----------
crust = find(c2, lambda it: it.get("a1_l3") == "甲壳类")
assert_eq(len(crust), 2, "表2 甲壳类(a1_l3='甲壳类') 行数应为2")
for it in crust:
    it["a1_l3"] = "甲壳类（例如：虾类、蟹类等）"
L(f"9. 表2 甲壳类 a1_l3 对齐 ×{len(crust)} 行")

# ---------- 10. 命名对齐 豆类 (表7) ----------
c7 = tbl(7)
beans = find(c7, lambda it: it.get("food") == "豆类")
assert_eq(len(beans), 1, "表7 豆类 行数应为1")
assert_eq(beans[0]["a1_l2"], "豆类", "表7 豆类 a1_l2 当前应为裸名'豆类'")
beans[0]["a1_l2"] = "豆类（干豆、以干豆磨成的粉）"
L(f"10. 表7 豆类 a1_l2 对齐")

# ---------- 11. 孤儿 repoint 黄酒 (表1) a1_l3→'' ----------
huangjiu = find(c1, lambda it: it.get("food") == "黄酒")
assert_eq(len(huangjiu), 1, "表1 黄酒 行数应为1")
assert_eq(huangjiu[0]["a1_l3"], "黄酒", "表1 黄酒 a1_l3 应为'黄酒'(孤儿)")
huangjiu[0]["a1_l3"] = ""
L(f"11. 表1 黄酒 a1_l3 '' (挂到 发酵酒 节点)")

# ---------- 12. 孤儿 repoint 水产动物油脂 (表11) a1_l3→'' ----------
c11 = tbl(11)
aqu = find(c11, lambda it: it.get("food") == "水产动物油脂")
assert_eq(len(aqu), 1, "表11 水产动物油脂 行数应为1")
assert_eq(aqu[0]["a1_l3"], "水产动物油脂", "表11 水产动物油脂 a1_l3 应为孤儿名")
aqu[0]["a1_l3"] = ""
L(f"12. 表11 水产动物油脂 a1_l3 '' (挂到 动物油脂 节点)")

# ---------- 13. 删 表2 畜禽肝/肾 无效挂载行 (肉制品›畜禽内脏) ----------
offal_invalid = find(c2, lambda it: it.get("food") in ("畜禽肝脏及其制品", "畜禽肾脏及其制品")
                     and it.get("a1_l2") == "肉制品（包括内脏制品、血制品）" and it.get("a1_l3") == "畜禽内脏")
assert_eq(len(offal_invalid), 2, "表2 畜禽 无效挂载行应为2")
offal_invalid_set = set(id(it) for it in offal_invalid)
c2["items"] = [it for it in c2["items"] if id(it) not in offal_invalid_set]
# 校验有效行仍在
offal_valid = find(c2, lambda it: it.get("food") in ("畜禽肝脏及其制品", "畜禽肾脏及其制品")
                   and it.get("a1_l3") == "畜禽内脏（例如：肝、肾、肺、肠等）")
assert_eq(len(offal_valid), 2, "表2 畜禽 有效挂载行应保留2")
L(f"13. 表2 删 畜禽肝/肾 无效挂载行 ×2 (有效行保留2)")

# ---------- 14. 表2 食用菌 6 组去重（按全字段去重，保留每条不同 a1 路径） ----------
DUP_GROUPS = [
    "芹菜、黄花菜",
    "香菇及其制品",
    "羊肚菌、獐头菌、青头菌、鸡油菌、榛蘑及以上食用菌的制品",
    "松茸、牛肝菌、鸡枞、多汁乳菇及以上食用菌的制品",
    "松露、姬松茸及以上食用菌的制品",
    "木耳及其制品、银耳及其制品",
]
KEYF = ["food","limit_value","a1_l1","a1_l2","a1_l3","a1_l4","note","modif","unit","sub_value","has_limit","pollutant"]
total_removed = 0
for food in DUP_GROUPS:
    grp = find(c2, lambda it, f=food: it.get("food") == f)
    if len(grp) < 2:
        raise SystemExit(f"[FATAL] 去重组 {food!r} 行数异常: {len(grp)}")
    # 每条不同(a1 路径)单独保留；同路径真重复只留1
    seen_paths = {}
    remove_ids = set()
    for it in grp:
        path = (it.get("a1_l1"), it.get("a1_l2"), it.get("a1_l3"), it.get("a1_l4"))
        fullkey = tuple(it.get(k) for k in KEYF)
        if path in seen_paths:
            # 同 a1 路径：再查全字段是否一致，一致才删（保险）
            if seen_paths[path] == fullkey:
                remove_ids.add(id(it))
            else:
                raise SystemExit(f"[FATAL] 同 a1 路径但全字段不同，中止 {food!r}: {seen_paths[path]} vs {fullkey}")
        else:
            seen_paths[path] = fullkey
    c2["items"] = [it for it in c2["items"] if id(it) not in remove_ids]
    total_removed += len(remove_ids)
    L(f"14. 表2 去重 {food!r}: {len(grp)}→{len(grp)-len(remove_ids)} (删 {len(remove_ids)}; 保留 a1 路径数={len(seen_paths)})")
    for p in seen_paths:
        L(f"      保留路径 {p}")
L(f"    去重合计删 {total_removed} 行")

# ---------- 收尾：更新 _last_fix ----------
data["_last_fix"] = "v82-fix97-notes-methods-spirulina-repoint-dedupe-2026-09-03"

# ---------- 写回 ----------
with open(P, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
L(f"\nDONE. 写回 {P}")
L(f"表2 现 items 数: {len(c2['items'])}")
