#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v82-fix82: L2 节点 ancestorsLevels 段显示 L1 通类 row

背景：
- v82-fix81 默认过滤 L1 通类 row(a1_l1!='' && a1_l2=='' && a1_l3=='' && a1_l4=='')
  防止 L3 节点机制层 fallback
- 但这导致 L2 节点 idx 空时也显示完全空(例:「蛋制品」L2 + 5 个 L3 全空)
- 用户决策: L2 节点 ancestorsLevels 段保留 L1 通类 row;L3+ 节点仍过滤 L1 通类 row
"""
from pathlib import Path

html_path = Path(r"C:\Users\10487\WorkBuddy\jianyu\jianyu-standalone-v82.html")
src = html_path.read_text(encoding="utf-8")

OLD = """      const filtered = items
        .filter(x => isApplicableToPath(x, ancestorPath))  // v78: ancestorPath
        // v82-fix81: 过滤 L1 通类 row（a1_l2='' a1_l3='' a1_l4='' 的 row）——机制层 fallback,不是 PDF 表达。
        //   例: idx=63「谷物及其制品〔...除外〕」L1 通类只在 L1 own row 显示,不再 fall back 给 L3 节点。
        //   L2 通类 row(a1_l2!='')保留显示——属于 PDF 表达覆盖,不是机制层 fallback。
        .filter(x => !(x.a1_l1 && !x.a1_l2 && !x.a1_l3 && !x.a1_l4))"""

NEW = """      const filtered = items
        .filter(x => isApplicableToPath(x, ancestorPath))  // v78: ancestorPath
        // v82-fix82: L2 节点(path.length===2)保留 L1 通类 row,L3+ 节点仍过滤 L1 通类 row。
        //   原因: 用户最新决策——L2 节点 idx 空时(如「蛋制品」),应当显示 L1 通类 row 作为 fallback。
        //   L3 节点仍按 v82-fix81 规则: 只显示 L2 通类 row,避免 L1 通类 row 机制层 fallback 到 L3。
        //   L1 通类 row 识别:a1_l1!='' && a1_l2=='' && a1_l3=='' && a1_l4==''
        .filter(x => {
          if (path.length === 2) return true;  // L2 节点:不过滤 L1 通类 row
          return !(x.a1_l1 && !x.a1_l2 && !x.a1_l3 && !x.a1_l4);  // L3+ 节点:过滤 L1 通类 row
        })"""

if OLD not in src:
    print("ERROR: 找不到 v82-fix81 过滤代码段,可能已修改过")
    raise SystemExit(1)

src2 = src.replace(OLD, NEW)

# bump 版本号
src2 = src2.replace(
    'v82-fix81-restore-ancestors-levels-filter-l1-2026-09-02',
    'v82-fix82-l2-show-l1-fallback-2026-09-02',
)

html_path.write_text(src2, encoding="utf-8")
print(f"v82-fix82 完成,文件大小: {len(src2)} bytes")
print(f"原 MD5: {hashlib.md5(src.encode()).hexdigest()}")
print(f"新 MD5: {hashlib.md5(src2.encode()).hexdigest()}")

import hashlib