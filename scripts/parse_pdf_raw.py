"""用 pdfplumber 抽取 GB 2762-2025 PDF 的所有表 1-12 原始数据(行 + 列 + 完整文本),
输出到 scripts/pdf_raw.json,供后续逐表重写。
"""
import json
import re
import pdfplumber

PDF = "data/gb2762/GB_2762-2025.pdf"
OUT = "scripts/pdf_raw.json"

with pdfplumber.open(PDF) as pdf:
    print(f"PDF 共 {len(pdf.pages)} 页")
    full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)

# 用 pdfplumber 抽表
tables_per_page = []
with pdfplumber.open(PDF) as pdf:
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
            print(f"  page {pi} 抽表失败: {e}")

print(f"共抽到 {len(tables_per_page)} 个表")
for tw in tables_per_page[:30]:
    print(f"  page {tw['page']} table#{tw['table_idx']} rows={len(tw['rows'])}")

# 保存
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"text": full_text, "tables": tables_per_page}, f, ensure_ascii=False, indent=2)
print(f"\n已保存到 {OUT}")

# 找表标题在文中位置
print("\n=== 文本中找表标题 ===")
for m in re.finditer(r"表\s*\d+\s+食品中[^\n]{1,50}限量", full_text):
    print(f" 位置 {m.start()}: {m.group()[:60]}")