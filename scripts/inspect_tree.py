# -*- coding: utf-8 -*-
import json

P = r"c:\Users\10487\WorkBuddy\jianyu\data\gb2762\gb2762_2025.json"
data = json.load(open(P, encoding="utf-8"))

tree = data["appendix_a1"]["tree"]

def walk(nodes, depth=0, path=""):
    for n in nodes:
        name = n.get("name","")
        catid = n.get("catid","")
        print("  "*depth + f"- {name!r}  catid={catid!r}")
        children = n.get("children") or []
        if children:
            walk(children, depth+1, path+"/"+name)

# Dump full tree to find exact node names
print("===== FULL A.1 TREE =====")
walk(tree)

print("\n===== search specific node names =====")
def find(name_sub, nodes, path=""):
    for n in nodes:
        nm = n.get("name","")
        full = path+"/"+nm
        if name_sub in nm:
            print("FOUND:", full, "| children:", [c.get("name") for c in (n.get("children") or [])])
        children = n.get("children") or []
        if children:
            find(name_sub, children, full)
for sub in ["牛肝菌","甲壳类","豆类","畜禽内脏","发酵酒","动物油脂","食用菌制品","肉类","肉制品","水产动物","藻类","坚果及籽类","生咖啡豆","花生","饮用天然矿泉水","包装饮用水","食用菌"]:
    print(f"\n--- contains {sub!r} ---")
    find(sub, tree)

print("\n===== 表7 铬: rows containing 豆类 =====")
cont = data["contaminants"]
for c in cont:
    if str(c.get("table_no")) == "7":
        for it in c["items"]:
            if "豆类" in (it.get("food") or "") or "豆类" in (it.get("a1_l2") or "") or "豆类" in (it.get("a1_l3") or ""):
                print("  food=",it.get("food"),"| a1=",(it.get("a1_l1"),it.get("a1_l2"),it.get("a1_l3"),it.get("a1_l4")),"| limit=",it.get("limit_value"))

print("\n===== 表2: all rows with 畜禽 / 内脏 in food or a1 =====")
for c in cont:
    if str(c.get("table_no")) == "2":
        for it in c["items"]:
            if "畜禽" in (it.get("food") or "") or "内脏" in (it.get("a1_l3") or "") or "内脏" in (it.get("food") or ""):
                print("  food=",it.get("food"),"| a1=",(it.get("a1_l1"),it.get("a1_l2"),it.get("a1_l3"),it.get("a1_l4")))
