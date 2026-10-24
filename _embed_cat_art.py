#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 data/gb2760/cat_art.js 内联进 gb2760.html（单文件、离线可用）
用法：python _embed_cat_art.py
"""
import re
import sys
from pathlib import Path

D = Path(__file__).parent
HTML = D / "gb2760.html"
ART = D / "data" / "gb2760" / "cat_art.js"

MARK_START = "/* ===== CAT_ART_INLINE_START ===== */"
MARK_END = "/* ===== CAT_ART_INLINE_END ===== */"


def main():
    art = ART.read_text(encoding="utf-8")
    # 去掉外层 window.CAT_ART = { } 包装，保留对象字面量
    m = re.search(r"window\.CAT_ART\s*=\s*(\{[\s\S]*\})\s*;?\s*$", art.strip())
    if not m:
        print("[X] 解析 cat_art.js 失败")
        return 1
    obj = m.group(1)
    # 重新包上赋值语句（内联后仍是独立 script 块，必须显式挂到 window）
    block_js = "window.CAT_ART = " + obj + ";"

    html = HTML.read_text(encoding="utf-8")
    if MARK_START in html:
        new_html = re.sub(
            re.escape(MARK_START) + r"[\s\S]*?" + re.escape(MARK_END),
            MARK_START + "\n" + block_js + "\n" + MARK_END,
            html,
        )
    else:
        # 插到主 <script> 标签内部的最前面（必须在 script 内，否则是无效代码）
        m = re.search(r"<script>\s*\n", html)
        if not m:
            print("[X] 未找到 script 标签")
            return 1
        idx = m.end()
        block = MARK_START + "\n" + block_js + "\n" + MARK_END + "\n\n"
        new_html = html[:idx] + block + html[idx:]

    HTML.write_text(new_html, encoding="utf-8")
    print("[OK] 已内联 CAT_ART，占用 %d 字符" % len(block_js))
    return 0


if __name__ == "__main__":
    sys.exit(main())
