#!/usr/bin/env python3
"""打包 jianyu 为单文件离线 HTML 应用。

输出位置：
  - 桌面: C:/Users/10487/Desktop/jianyu-offline.html
  - 工作台: C:/Users/10487/WorkBuddy/jianyu/jianyu-offline.html

用法：
  python build_offline.py            # 默认桌面 + 工作台
  python build_offline.py --out X    # 自定义输出路径
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\Users\10487\WorkBuddy\jianyu")
DATA_DIR = ROOT / "data"

# 内嵌的 5 个数据文件（key → 相对路径）
DATA_FILES = {
    "master":              "master.json",
    "category_map":        "category_map.json",
    "subcat_to_items":     "subcat_to_items.json",
    "gb_checklist_subcat": "current_period/gb_checklist_subcat.json",
    "categories_2026":     "categories_2026.json",
}


def load_all_data():
    """读 5 个 JSON，返回 dict（key 对应 DATA_FILES 的 key）。"""
    out = {}
    for key, rel in DATA_FILES.items():
        p = DATA_DIR / rel
        if not p.exists():
            print(f"❌ 缺少 {p}", file=sys.stderr)
            sys.exit(1)
        with open(p, "r", encoding="utf-8") as f:
            out[key] = json.load(f)
        size_kb = p.stat().st_size / 1024
        print(f"  ✓ {rel:55s} {size_kb:>7.1f} KB")
    return out


def build_inline_html(data: dict) -> str:
    """读 index.html 模板，把 fetch 改为读内嵌对象。"""
    src = (ROOT / "index.html").read_text(encoding="utf-8")

    # 1) loadData() 改为同步读 window.__JIANYU_DATA__
    old_load = """async function loadData() {
  try {
    const [master, cm, subcatItems, subcatChecklist, categories] = await Promise.all([
      fetch('data/master.json').then(r => r.json()),
      fetch('data/category_map.json').then(r => r.json()),
      fetch('data/subcat_to_items.json').then(r => r.json()),
      fetch('data/current_period/gb_checklist_subcat.json').then(r => r.json()),
      fetch('data/categories_2026.json').then(r => r.json()),
    ]);"""

    new_load = """function loadData() {
  try {
    // 单文件离线版：数据从 window.__JIANYU_DATA__ 读（同步）
    const D = window.__JIANYU_DATA__;
    const master = D.master;
    const cm = D.category_map;
    const subcatItems = D.subcat_to_items;
    const subcatChecklist = D.gb_checklist_subcat;
    const categories = D.categories_2026;"""

    if old_load not in src:
        print("❌ index.html 中找不到 loadData() 模板，脚本可能过期", file=sys.stderr)
        sys.exit(2)
    src = src.replace(old_load, new_load)

    # 2) catch 块里去掉 fetch 失败的提示（不会触发了，但保留以防万一）
    # 不动

    # 3) 在 <script> 之前注入数据
    # 数据用 JSON.stringify，无 indent（减小体积）
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    inject = f"""<script>
  // 离线版数据快照（{datetime.now().strftime('%Y-%m-%d %H:%M')}）
  window.__JIANYU_DATA__ = {data_json};
</script>
</body>"""

    # 把 </body> 替换为内嵌脚本 + </body>
    src = src.replace("</body>", inject, 1)

    # 4) 在 <title> 后加注释
    title_marker = "</title>"
    offline_marker = (
        "  <!-- 单文件离线版（无网络依赖），双击在浏览器打开即可 -->\n"
    )
    src = src.replace(title_marker, title_marker + "\n" + offline_marker, 1)

    return src


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="输出路径（默认写到桌面 + 工作台）")
    args = parser.parse_args()

    print("== 读取数据 ==")
    data = load_all_data()

    print("\n== 拼接 HTML ==")
    html = build_inline_html(data)

    # 输出位置
    targets = []
    if args.out:
        targets.append(Path(args.out))
    else:
        targets.append(Path(r"C:\Users\10487\Desktop\jianyu-offline.html"))
        targets.append(ROOT / "jianyu-offline.html")

    print("\n== 写入文件 ==")
    for t in targets:
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(html, encoding="utf-8")
        size_kb = t.stat().st_size / 1024
        print(f"  ✓ {t}  ({size_kb:.1f} KB)")

    print("\n完成。伙伴收到 .html 后双击即可在浏览器打开（无需联网）。")


if __name__ == "__main__":
    main()
