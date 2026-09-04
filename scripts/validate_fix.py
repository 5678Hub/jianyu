# -*- coding: utf-8 -*-
import json

CUR = r"c:\Users\10487\WorkBuddy\jianyu\data\gb2762\gb2762_2025.json"
BAK = r"c:\Users\10487\WorkBuddy\jianyu\data\gb2762\gb2762_2025.json.bak.v82fix_all_20260903"

cur = json.load(open(CUR, encoding="utf-8"))
bak = json.load(open(BAK, encoding="utf-8"))

cb = {str(c["table_no"]): c for c in cur["contaminants"]}
bb = {str(c["table_no"]): c for c in bak["contaminants"]}

ok = True
def check(name, cond, detail=""):
    global ok
    status = "PASS" if cond else "FAIL"
    if not cond: ok = False
    print(f"[{status}] {name} {detail}")

print("===== A. 各表 item 数变化（应仅 1/2/7/8/11 变化） =====")
allt = sorted(set(cb) | set(bb), key=int)
for t in allt:
    nc = len(cb[t]["items"]) if t in cb else 0
    nb = len(bb[t]["items"]) if t in bb else 0
    mark = "" if nc == nb else "  <-- 变化"
    print(f"  表{t}: before={nb} after={nc}{mark}")

print("\n===== B. 表1 校验 =====")
c1 = cb["1"]; b1 = bb["1"]
check("表1 生咖啡豆 note 已清空(2行)",
      sum(1 for it in c1["items"] if it.get("food")=="生咖啡豆及烘焙咖啡豆" and it.get("note")=="d")==0)
check("表1 footnotes 无 label=d",
      not any(f.get("label")=="d" for f in c1["footnotes"]), f"labels={[f['label'] for f in c1['footnotes']]}")
sp = [it for it in c1["items"] if it.get("food")=="螺旋藻"]
check("表1 螺旋藻 limit=2.0(干重计)",
      len(sp)==1 and sp[0]["limit_value"]=="2.0(干重计)", f"got {[s.get('limit_value') for s in sp]}")
hj = [it for it in c1["items"] if it.get("food")=="黄酒"]
check("表1 黄酒 a1_l3 已置空", len(hj)==1 and hj[0]["a1_l3"]=="", f"a1_l3={[h.get('a1_l3') for h in hj]}")

print("\n===== C. 表2 校验 =====")
c2 = cb["2"]; b2 = bb["2"]
check("表2 花生 note 已清空(2行)",
      sum(1 for it in c2["items"] if it.get("food")=="花生" and it.get("note")=="b")==0)
check("表2 footnotes 无 label=b",
      not any(f.get("label")=="b" for f in c2["footnotes"]), f"labels={[f['label'] for f in c2['footnotes']]}")
check("表2 rules[0].apply=包装饮用水",
      c2["inspection_method_rules"][0]["apply"]=="包装饮用水" and "GB 8538" in c2["inspection_method_rules"][0]["method"])
check("表2 rules 末条仍为 default(GB5009.15)",
      c2["inspection_method_rules"][-1].get("is_default") is True and "GB 5009.15" in c2["inspection_method_rules"][-1]["method"])
check("表2 表级句含 包装饮用水→GB8538",
      "GB 8538" in c2["inspection_method"] and "GB 5009.15" in c2["inspection_method"])
# 牛肝菌对齐
bo = [it for it in c2["items"] if it.get("food")=="松茸、牛肝菌、鸡枞、多汁乳菇及以上食用菌的制品"]
check("表2 牛肝菌 a1_l3 已对齐", any(it["a1_l3"].startswith("牛肝菌[") for it in bo), f"a1_l3={[b.get('a1_l3') for b in bo]}")
# 甲壳类对齐(2行)
cr = [it for it in c2["items"] if it.get("a1_l3")=="甲壳类（例如：虾类、蟹类等）"]
check("表2 甲壳类(对齐后) 行数=2", len(cr)==2, f"got {len(cr)}")
check("表2 无裸名 a1_l3='甲壳类'", not any(it.get("a1_l3")=="甲壳类" for it in c2["items"]))
check("表2 无裸名 a1_l3='牛肝菌'", not any(it.get("a1_l3")=="牛肝菌" for it in c2["items"]))
# 畜禽无效挂载已删
off_inv = [it for it in c2["items"] if it.get("food") in ("畜禽肝脏及其制品","畜禽肾脏及其制品")
           and it.get("a1_l2")=="肉制品（包括内脏制品、血制品）" and it.get("a1_l3")=="畜禽内脏"]
check("表2 畜禽 无效挂载行已删(0)", len(off_inv)==0)
off_val = [it for it in c2["items"] if it.get("food") in ("畜禽肝脏及其制品","畜禽肾脏及其制品")
           and it.get("a1_l3")=="畜禽内脏（例如：肝、肾、肺、肠等）"]
check("表2 畜禽 有效挂载行保留(2)", len(off_val)==2, f"got {len(off_val)}")
# 去重后各组至少保留1
for food in ["芹菜、黄花菜","香菇及其制品","羊肚菌、獐头菌、青头菌、鸡油菌、榛蘑及以上食用菌的制品",
             "松茸、牛肝菌、鸡枞、多汁乳菇及以上食用菌的制品","松露、姬松茸及以上食用菌的制品","木耳及其制品、银耳及其制品"]:
    n = sum(1 for it in c2["items"] if it.get("food")==food)
    check(f"表2 去重后保留 {food[:10]}… 行数>=1", n>=1, f"got {n}")

print("\n===== D. 表7 校验 =====")
c7 = cb["7"]
beans = [it for it in c7["items"] if it.get("food")=="豆类"]
check("表7 豆类 a1_l2 已对齐", len(beans)==1 and beans[0]["a1_l2"]=="豆类（干豆、以干豆磨成的粉）", f"a1_l2={[b.get('a1_l2') for b in beans]}")

print("\n===== E. 表8 校验 =====")
c8 = cb["8"]
ee = [f for f in c8["footnotes"] if f.get("label")=="e"]
check("表8 脚注 e 已对齐 PDF", len(ee)==1 and ee[0]["text"]=="仅适用于乳基产品(不含豆类成分)。", f"got {ee}")

print("\n===== F. 表11 校验 =====")
c11 = cb["11"]
aq = [it for it in c11["items"] if it.get("food")=="水产动物油脂"]
check("表11 水产动物油脂 a1_l3 已置空", len(aq)==1 and aq[0]["a1_l3"]=="" , f"a1_l3={[a.get('a1_l3') for a in aq]}")

print("\n===== G. A.1 树未被改动 =====")
check("appendix_a1 与备份一致", json.dumps(cur["appendix_a1"], ensure_ascii=False, sort_keys=True)
      == json.dumps(bak["appendix_a1"], ensure_ascii=False, sort_keys=True))

print("\n===== H. 其他表 items 字节一致（除 1/2/7/8/11） =====")
for t in allt:
    if t in ("1","2","7","8","11"): continue
    if t not in cb or t not in bb: 
        check(f"表{t} 存在性", False); continue
    same = json.dumps(cb[t]["items"], ensure_ascii=False, sort_keys=True) == json.dumps(bb[t]["items"], ensure_ascii=False, sort_keys=True)
    check(f"表{t} items 未变", same)

print("\n===== I. 顶层结构 =====")
check("_last_fix 已更新", cur.get("_last_fix","").startswith("v82-fix"), cur.get("_last_fix"))
for k in ["standard","application_principles","contaminants","appendix_a1","additives"]:
    check(f"顶层 key {k} 存在", k in cur)

print("\n" + ("ALL CHECKS PASSED ✅" if ok else "SOME CHECKS FAILED ❌"))
import sys
sys.exit(0 if ok else 1)
