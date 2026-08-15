"""按文本位置切分 PDF 12 张表的完整文本(从标题到下一标题前),并把脚注 a/b/c/d... 提取出来。"""
import json
import re

with open("scripts/pdf_raw.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

text = raw["text"]

# 表标题位置
title_pattern = re.compile(r"表(\d+)\s+食品中([^\n]{1,40})限量")
matches = list(title_pattern.finditer(text))
print(f"找到 {len(matches)} 个表标题")

# 切片
tables = []
for i, m in enumerate(matches):
    table_no = int(m.group(1))
    content = m.group(2).strip()
    start = m.start()
    end = matches[i+1].start() if i+1 < len(matches) else len(text)
    chunk = text[start:end].strip()

    # 提取脚注 a/b/c/d
    footnotes = []
    for fm in re.finditer(r"([a-z])\s+([^\n]{2,200})", chunk):
        label = fm.group(1)
        ftxt = fm.group(2).strip()
        # 过滤非脚注
        if ftxt.startswith("仅") or ftxt.startswith("对") or ftxt.startswith("由于") or ftxt.startswith("制品") or ftxt.startswith("其") or ftxt.startswith("在") or ftxt.startswith("指") or ftxt.startswith("按") or ftxt.startswith("以") or ftxt.startswith("总") or ftxt.startswith("不") or ftxt.startswith("生") or ftxt.startswith("对"):
            footnotes.append({"label": label, "text": ftxt})
        elif len(ftxt) < 80 and ("类" in ftxt or "计" in ftxt or "度" in ftxt or "等" in ftxt or "时" in ftxt or "算" in ftxt or "可" in ftxt or "者" in ftxt or "须" in ftxt or "已" in ftxt or "于" in ftxt or "样" in ftxt):
            footnotes.append({"label": label, "text": ftxt})

    tables.append({
        "table_no": table_no,
        "title": f"表{table_no} {content}",
        "text": chunk,
        "footnotes": footnotes,
    })

# 标题名 + 起始 200 字符
for tb in tables:
    print(f"\n=== 表{tb['table_no']} {tb['title']} ===")
    print(f"  文本长度: {len(tb['text'])}")
    print(f"  前 400 字: {tb['text'][:400]}")
    print(f"  脚注: {tb['footnotes']}")

with open("scripts/pdf_tables.json", "w", encoding="utf-8") as f:
    json.dump(tables, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 scripts/pdf_tables.json")