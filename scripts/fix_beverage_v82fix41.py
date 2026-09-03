#!/usr/bin/env python3
"""v82-fix41: 修正饮料类「按污染查询」页面的层级结构，对齐 PDF 表 1

PDF 表 1 饮料类结构:
  饮料类(除外): 0.3
    包装饮用水: 0.01 mg/L
    含乳饮料: 0.05
    果蔬汁类及其饮料(除外): 0.03
      含浆果及小粒水果的果蔬汁类及其饮料(葡萄汁除外): 0.05
        葡萄汁: 0.04
      浓缩果蔬汁(浆): 0.5
    固体饮料: 1.0

问题：3 条 row 的 a1_l3/a1_l4 为空，导致「按污染查询」渲染时:
  - 含浆果及小粒水果的果蔬汁类及其饮料(葡萄汁除外) 缩进到 depth 2（应在 depth 3）
  - 葡萄汁 缩进到 depth 2（应在 depth 4）
  - 浓缩果蔬汁(浆) 已有 a1_l3=浓缩果蔬汁（浆）（depth 3，正确）

修复：
1. tree 加节点：果蔬汁类及其饮料 > 含浆果及小粒水果的果蔬汁类及其饮料（葡萄汁除外） > 葡萄汁
2. items 改 a1_l3：含浆果... row 设 a1_l3=含浆果及小粒水果的果蔬汁类及其饮料（葡萄汁除外）
3. items 改 a1_l3+a1_l4：葡萄汁 row 设 a1_l3=含浆果..., a1_l4=葡萄汁
4. bump v82-fix40 → v82-fix41
"""
import json
import sys
from pathlib import Path

FILE = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
BACKSLASH = chr(92); QUOTE = chr(34)

html = FILE.read_text(encoding="utf-8")
start_tag = '<script type="application/json" id="inlineData">'
end_tag = '</script>'
start = html.index(start_tag) + len(start_tag)
depth = 0; in_str = False; esc = False; obj_end = -1
for off in range(start, len(html)):
    ch = html[off]
    if in_str:
        if esc: esc = False
        elif ch == BACKSLASH: esc = True
        elif ch == QUOTE: in_str = False
        continue
    if ch == QUOTE: in_str = True
    elif ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: obj_end = off + 1; break
if obj_end == -1:
    sys.exit("ERROR: inlineData JSON not found")

raw_json = html[start:obj_end]
data = json.loads(raw_json)

# 1) tree: 在「果蔬汁类及其饮料」节点下新增「含浆果及小粒水果的果蔬汁类及其饮料（葡萄汁除外）」，
#           该节点下新增「葡萄汁」
tree = data["appendix_a1"]["tree"]
target_l2_name = "果蔬汁类及其饮料（例如：苹果汁、苹果醋饮料、山楂汁、山楂醋饮料等）"
new_l3_name = "含浆果及小粒水果的果蔬汁类及其饮料（葡萄汁除外）"
new_l4_name = "葡萄汁"

# 找最大 catid 以分配新节点
max_catid = 0
def walk_max(node):
    global max_catid
    if isinstance(node, dict):
        cid = node.get("catid")
        if isinstance(cid, int):
            max_catid = max(max_catid, cid)
        for v in node.values():
            walk_max(v)
    elif isinstance(node, list):
        for v in node:
            walk_max(v)
walk_max(tree)
print(f"Max catid in tree: {max_catid}")

# 插入新节点
inserted_l3 = False
for n1 in tree:
    if n1.get("name") != "饮料类":
        continue
    for c in n1.get("children", []):
        if c.get("name") != target_l2_name:
            continue
        # 找 max catid 在该子树
        subtree_max = [0]
        def sub_max(n):
            if isinstance(n, dict):
                cid = n.get("catid")
                if isinstance(cid, int):
                    if cid > subtree_max[0]:
                        subtree_max[0] = cid
                for v in n.values():
                    sub_max(v)
            elif isinstance(n, list):
                for v in n:
                    sub_max(v)
        sub_max(c)
        new_l3_id = subtree_max[0] + 1
        new_l4_id = subtree_max[0] + 2
        # 新 L3
        l3_node = {
            "catid": new_l3_id,
            "name": new_l3_name,
            "children": [
                {"catid": new_l4_id, "name": new_l4_name, "children": []}
            ],
        }
        # 插入到 children 列表最前（PDF 顺序：含浆果... 在前）
        c.setdefault("children", []).insert(0, l3_node)
        inserted_l3 = True
        print(f"Inserted tree node: {new_l3_name} (catid={new_l3_id}) > {new_l4_name} (catid={new_l4_id})")
        break
    if inserted_l3:
        break

if not inserted_l3:
    sys.exit("ERROR: 饮料类 > 果蔬汁类及其饮料 node not found")

# 2) items: 改 a1_l3/a1_l4
lead = next((c for c in data["contaminants"] if c.get("symbol") == "Pb"), None)
if lead is None:
    sys.exit("ERROR: lead contaminant block not found")

items = lead["items"]
fixed = []
for i, it in enumerate(items):
    food = it.get("food", "")
    l2 = it.get("a1_l2", "")
    # 仅处理饮料类 + 果蔬汁类及其饮料 子树
    if it.get("a1_l1") != "饮料类":
        continue
    if l2 != target_l2_name:
        continue
    if food == "含浆果及小粒水果的果蔬汁类及其饮料(葡萄汁除外)":
        it["a1_l3"] = new_l3_name
        it["a1_l4"] = ""
        fixed.append((i, "含浆果... a1_l3 set"))
    elif food == "葡萄汁":
        it["a1_l3"] = new_l3_name
        it["a1_l4"] = new_l4_name
        fixed.append((i, "葡萄汁 a1_l3+a1_l4 set"))
    elif food == "浓缩果蔬汁(浆)":
        # 已正确，不动
        pass

for idx, msg in fixed:
    print(f"  items[{idx}]: {msg}")

# 写回
new_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
new_html = html[:start] + new_json + html[obj_end:]

# bump 版本号 3 处（meta / CACHE_BUST / title）
OLD_META = "v82-fix40-lead-rice-05-to-02-2026-09-01"
NEW_META = "v82-fix41-beverage-pdf-hier-2026-09-01"
OLD_TITLE = "[v82-fix40]"
NEW_TITLE = "[v82-fix41]"

n1 = new_html.count(OLD_META)
new_html = new_html.replace(OLD_META, NEW_META)
n2 = new_html.count(OLD_TITLE)
new_html = new_html.replace(OLD_TITLE, NEW_TITLE)
print(f"Bumped meta/CACHE_BUST: {n1} places")
print(f"Bumped title: {n2} places")

FILE.write_text(new_html, encoding="utf-8")
print("OK")