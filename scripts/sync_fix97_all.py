# -*- coding: utf-8 -*-
"""v82-fix97 全量同步：把已修正的 gb2762_2025.json 同步到所有内嵌副本。
- 源 JSON：jianyu/data/gb2762/gb2762_2025.json（已修正）
- JSON 副本：抽检不合格查询助手 / 工作台
- inlineData 副本（jianyu-standalone-v82.html）：jianyu(源) / 抽检 / 工作台
不涉及 gb2762/gb2762.html（其 embedded 为另一套 schema，非本数据副本）。
"""
import json, shutil, os, sys, hashlib

ROOT = r"C:\Users\10487\WorkBuddy"
SRC_JSON = os.path.join(ROOT, "jianyu", "data", "gb2762", "gb2762_2025.json")

JSON_TARGETS = [
    os.path.join(ROOT, "抽检不合格查询助手", "data", "gb2762", "gb2762_2025.json"),
    os.path.join(ROOT, "工作台", "data", "gb2762", "gb2762_2025.json"),
]
HTML_TARGETS = [
    os.path.join(ROOT, "jianyu", "jianyu-standalone-v82.html"),
    os.path.join(ROOT, "抽检不合格查询助手", "jianyu-standalone-v82.html"),
    os.path.join(ROOT, "工作台", "jianyu-standalone-v82.html"),
]
BAK = ".bak.v82fix97_sync"

def md5(p):
    with open(p, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_src():
    with open(SRC_JSON, encoding="utf-8") as f:
        return json.load(f)

def copy_json(target):
    if not os.path.exists(target):
        print(f"  ✗ 跳过(不存在) {target}")
        return False
    bak = target + BAK
    if not os.path.exists(bak):
        shutil.copy(target, bak)
    shutil.copy(SRC_JSON, target)
    print(f"  ✓ JSON 同步 {os.path.relpath(target, ROOT)}  (备份 {os.path.basename(bak)})")
    return True

def sync_inline(html_path, src_data):
    if not os.path.exists(html_path):
        print(f"  ✗ 跳过(不存在) {html_path}")
        return False
    bak = html_path + BAK
    if not os.path.exists(bak):
        shutil.copy(html_path, bak)
    html = open(html_path, encoding="utf-8").read()
    start_marker = '<script type="application/json" id="inlineData">'
    sp = html.find(start_marker)
    if sp < 0:
        print(f"  ✗ 未找到 inlineData 标记，回退备份 {html_path}")
        return False
    ep = html.find("</script>", sp)
    if ep < 0:
        print(f"  ✗ 未找到 </script>，回退备份 {html_path}")
        return False
    json_str = json.dumps(src_data, ensure_ascii=False, indent=2)
    new_html = html[:sp] + start_marker + "\n" + json_str + "\n" + html[ep:]
    open(html_path, "w", encoding="utf-8").write(new_html)
    # validate
    rd = open(html_path, encoding="utf-8").read()
    s2 = rd.find(start_marker) + len(start_marker)
    e2 = rd.find("</script>", s2)
    try:
        obj = json.loads(rd[s2:e2])
        n = len(obj["contaminants"])
        ok_fix = obj.get("_last_fix", "").startswith("v82-fix97")
        print(f"  ✓ inlineData 同步 {os.path.relpath(html_path, ROOT)} (contaminants={n}, _last_fix={ok_fix})")
        return True
    except Exception as e:
        print(f"  ✗ 校验失败 {e}，回退备份")
        shutil.copy(bak, html_path)
        return False

def main():
    src = load_src()
    print(f"源 JSON: {os.path.relpath(SRC_JSON, ROOT)}  contaminants={len(src['contaminants'])}  _last_fix={src.get('_last_fix')}\n")
    print("-- 同步 JSON 副本 --")
    for t in JSON_TARGETS:
        copy_json(t)
    print("\n-- 同步 inlineData (含源 HTML) --")
    for t in HTML_TARGETS:
        sync_inline(t, src)
    print("\n-- JSON MD5 一致性 --")
    json_files = [SRC_JSON] + JSON_TARGETS
    md5s = {}
    for f in json_files:
        if os.path.exists(f):
            m = md5(f); md5s[f] = m
            print(f"  {m[:10]}… {os.path.relpath(f, ROOT)}")
    vals = set(md5s.values())
    print(f"  {'✓ 全部一致' if len(vals)==1 else '✗ 不一致: '+str(vals)}")
    # 校验内容：从源 HTML inlineData 抽一条关键修复
    print("\n-- 关键修复在源 HTML 中的存在性 --")
    h = open(HTML_TARGETS[0], encoding="utf-8").read()
    sp = h.find('<script type="application/json" id="inlineData">') + len('<script type="application/json" id="inlineData">')
    ep = h.find("</script>", sp)
    obj = json.loads(h[sp:ep])
    c2 = next(c for c in obj["contaminants"] if str(c["table_no"])=="2")
    c1 = next(c for c in obj["contaminants"] if str(c["table_no"])=="1")
    print("  表2 rules[0].apply =", c2["inspection_method_rules"][0]["apply"])
    print("  表1 螺旋藻 limit =", [it["limit_value"] for it in c1["items"] if it["food"]=="螺旋藻"])
    print("  表1 footnotes labels =", [f["label"] for f in c1["footnotes"]])
    print("  表2 footnotes labels =", [f["label"] for f in c2["footnotes"]])

if __name__ == "__main__":
    main()
