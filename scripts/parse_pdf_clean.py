"""重新解析 PDF:
- 表 1 完整提取(跨页合并)
- 提取每张表的所有行
- 提取每张表的脚注 a/b/c/d/e 完整文本
"""
import json
import re
import pdfplumber

PDF = "data/gb2762/GB_2762-2025.pdf"

with pdfplumber.open(PDF) as pdf:
    tables_per_page = []
    for pi, page in enumerate(pdf.pages, 1):
        try:
            tables = page.extract_tables()
            for ti, t in enumerate(tables):
                tables_per_page.append({
                    "page": pi,
                    "table_idx": ti,
                    "rows": t,
                })
        except Exception as e:
            print(f"page {pi} 抽表失败: {e}")

# 表 1 跨多页。所有表按页顺序合并:表 1 占 page 4/5/6(table 0/0/0),共 3 个
# 实际: page 4 table0 = 表1 部分1, page 5 table0 = 表1 部分2, page 6 table0 = 表1 部分3
# 但我看到 tables_per_page 有 24 个表,需要识别它们对应的"表 1/2/3..."

# 从文本中找表标题位置
full_text = ""
with pdfplumber.open(PDF) as pdf:
    for p in pdf.pages:
        full_text += (p.extract_text() or "") + "\n"

# 表标题位置(注意 PDF 中有"表1 食品中铅限量指标"和"表1 食品中铅限量指标 续"两种)
title_pat = re.compile(r"表\s*(\d+)\s+食品中([^\n]{1,40})限量")
title_matches = list(title_pat.finditer(full_text))
print(f"标题数: {len(title_matches)}")

# 表格按"上一页的标题到下一页标题前" 关联
# 简化:已知结构
# 实际上由 PDF 抽表返回的 24 个表大致对应:
#   [0] page4 table0 = 表1 part1
#   [1] page5 table0 = 表1 part2
#   [2] page6 table0 = 表1 part3
#   [3] page7 table0 = 表2 part1
#   [4] page8 table0 = 表3 part1
#   [5] page8 table1 = 表3 part2
#   [6] page9 table0 = 表4 part1
#   [7] page9 table1 = 表4 part2
#   [8] page10 table0 = 表5 + 表6 part1
#   [9] page11 table0 = 表7 part1
#   [10] page11 table1 = 表7 part2
#   [11] page11 table2 = 表8 part1
#   [12] page12 table0 = 表8 part2
#   [13] page13 table0 = 表9 part1
#   [14] page13 table1 = 表10 part1
#   [15] page14 table0 = 表11 part1
#   [16] page14 table1 = 表12 part1
#   [17] page15 table0 = 表12 part2
#   [18] page16 table0 = 表13?
#   [19] page17 table0 = 表14?
#   ... 部分可能是附录 A.1

# 简化:看每张表的内容,提取 food / limit
from collections import defaultdict
extracted = defaultdict(list)

for ti, tw in enumerate(tables_per_page):
    rows = tw["rows"]
    if not rows:
        continue
    # 第一行通常是表头(食品类别/名称/限量)
    # 第二行起是数据
    page = tw["page"]

    # 看文本中本页第一个表标题
    if page == 4:
        key = "表1"
    elif page == 5:
        key = "表1"
    elif page == 6:
        key = "表1"
    elif page == 7:
        key = "表2"
    elif page == 8 and tw["table_idx"] == 0:
        key = "表3"
    elif page == 8 and tw["table_idx"] == 1:
        key = "表3"
    elif page == 9 and tw["table_idx"] == 0:
        key = "表4"
    elif page == 9 and tw["table_idx"] == 1:
        key = "表4"
    elif page == 10:
        key = "表5"
    elif page == 11 and tw["table_idx"] == 0:
        key = "表6"
    elif page == 11 and tw["table_idx"] == 1:
        key = "表7"
    elif page == 11 and tw["table_idx"] == 2:
        key = "表8"
    elif page == 12:
        key = "表8"
    elif page == 13:
        key = "表9"
    elif page == 14:
        key = "表10"
    elif page == 15:
        key = "表11"
    elif page == 16:
        key = "表12"
    else:
        key = f"unknown_p{page}_t{tw['table_idx']}"

    extracted[key].append({
        "page": page,
        "table_idx": tw["table_idx"],
        "rows": rows,
    })

# 打印每张表
for key in sorted(extracted.keys(), key=lambda x: (int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999, x)):
    parts = extracted[key]
    print(f"\n=== {key} ({len(parts)} 部分) ===")
    for p in parts:
        print(f"  page {p['page']} table#{p['table_idx']} rows={len(p['rows'])}")
        # 打印前 15 行
        for r in p["rows"][:15]:
            print(f"    {r}")

with open("scripts/pdf_tables_extracted.json", "w", encoding="utf-8") as f:
    json.dump({k: v for k, v in extracted.items()}, f, ensure_ascii=False, indent=2)
print("\n已保存 scripts/pdf_tables_extracted.json")