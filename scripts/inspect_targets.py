# -*- coding: utf-8 -*-
import json, sys

P = r"c:\Users\10487\WorkBuddy\jianyu\data\gb2762\gb2762_2025.json"
data = json.load(open(P, encoding="utf-8"))

cont = data["contaminants"]

def find_table(tno):
    for c in cont:
        if str(c.get("table_no")) == str(tno):
            return c
    return None

def dump_item(it, tag=""):
    print(f"  [{tag}] food={it.get('food')!r} | table_no={it.get('table_no')} pollutant={it.get('pollutant')!r}")
    print(f"       limit_value={it.get('limit_value')!r} has_limit={it.get('has_limit')} sub={it.get('sub_value')!r} unit={it.get('unit')!r} modif={it.get('modif')!r}")
    print(f"       note={it.get('note')!r} remark={it.get('remark')!r} main_remark={it.get('main_remark')!r} sub_remark={it.get('sub_remark')!r}")
    print(f"       im={it.get('inspection_method')!r} sub_im={it.get('sub_inspection_method')!r}")
    print(f"       a1_l1={it.get('a1_l1')!r} a1_l2={it.get('a1_l2')!r} a1_l3={it.get('a1_l3')!r} a1_l4={it.get('a1_l4')!r}")
    print(f"       sub_label={it.get('sub_label')!r} main_label={it.get('main_label')!r}")

print("===== 0. table-level footnotes & rules =====")
for tno in [1,2,8]:
    c = find_table(tno)
    print(f"\n--- 表{tno} ({c.get('contaminant')}) ---")
    print("  footnotes:", json.dumps(c.get("footnotes"), ensure_ascii=False))
    print("  inspection_method_rules:", json.dumps(c.get("inspection_method_rules"), ensure_ascii=False))
    print("  inspection_method(table-level sentence):", c.get("inspection_method"))

print("\n===== 1. 表1 生咖啡豆 note='d' =====")
c1 = find_table(1)
for it in c1["items"]:
    if it.get("note") == "d" or "生咖啡豆" in (it.get("food") or ""):
        dump_item(it, "T1-coffee")

print("\n===== 2. 表2 花生 note='b' =====")
c2 = find_table(2)
for it in c2["items"]:
    if it.get("note") == "b" or (it.get("food") and "花生" in it["food"]):
        dump_item(it, "T2-peanut")

print("\n===== 4. 表2 包装饮用水 / 饮用天然矿泉水 =====")
for it in c2["items"]:
    if it.get("food") and ("包装饮用水" in it["food"] or "饮用天然矿泉水" in it["food"]):
        dump_item(it, "T2-water")

print("\n===== 5. 表1 螺旋藻 (limit) =====")
for it in c1["items"]:
    if it.get("food") and "螺旋藻" in it["food"]:
        dump_item(it, "T1-spirulina")

print("\n===== 6. 黄酒 (a1_l3=黄酒) / 水产动物油脂 (a1_l3=水产动物油脂) =====")
for c in cont:
    for it in c["items"]:
        if it.get("a1_l3") in ("黄酒", "水产动物油脂"):
            dump_item(it, f"T{c.get('table_no')}-orphan")

print("\n===== 7. name align: 牛肝菌 / 甲壳类 / 豆类 =====")
for c in cont:
    for it in c["items"]:
        l3 = it.get("a1_l3") or ""
        if l3 == "牛肝菌" or l3 == "甲壳类" or l3 == "豆类":
            dump_item(it, f"T{c.get('table_no')}-namealign")

print("\n===== 8. 畜禽肝/肾 invalid path (肉制品›畜禽内脏) =====")
for c in cont:
    for it in c["items"]:
        if it.get("a1_l3") == "畜禽内脏":
            dump_item(it, f"T{c.get('table_no')}-offal")

print("\n===== 9. 表2 食用菌 duplicate groups =====")
# group by (food, limit_value, a1_l1,l2,l3,l4, note) approximate
from collections import defaultdict
groups = defaultdict(list)
for it in c2["items"]:
    f = it.get("food") or ""
    if any(k in f for k in ["食用菌","香菇","木耳","银耳","牛肝菌","松茸","羊肚菌","松露","芹菜","黄花菜","鸡枞","多汁乳菇","姬松茸","獐头菌","青头菌","鸡油菌","榛蘑"]):
        key = (f, it.get("limit_value"), it.get("a1_l1"), it.get("a1_l2"), it.get("a1_l3"), it.get("a1_l4"))
        groups[key].append(it)
for key, its in groups.items():
    if len(its) > 1:
        print(f"\n  DUPLICATE GROUP (n={len(its)}): food={key[0]!r} limit={key[1]!r} a1=({key[2]!r},{key[3]!r},{key[4]!r},{key[5]!r})")
        for it in its:
            print(f"     id-like(food)={it.get('food')!r} note={it.get('note')!r} modif={it.get('modif')!r}")
