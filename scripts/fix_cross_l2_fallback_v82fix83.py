"""v82-fix83: 跨 L2 漏显示 fallback 段

策略（用户确认）：
- L3 idx 空节点 ancestorsLevels 段应显示「同 L1 章节下所有 L2 通类 row + L1 通类 row」
- 实施：在已有祖先分层段（ancestorPath 分段）之后，新增一个「跨 L2 通类 row 段」
- 仅当 path.length === 3 且 primaryItems.length === 0 时显示
- 收集「a1l1=path[0], a1l2!=path[1], a1l3='', a1l4=''」的 row
- 排除 ancestorsLevels 段已显示的 row（用 dedupKey 去重）
- 标签：「同章节其他 L2 通类 row 赋予的污染物限量要求」
"""
import re

PATH = 'jianyu-standalone-v82.html'
with open(PATH, 'r', encoding='utf-8') as f:
    html = f.read()

OLD = '''      if (filtered.length === 0) continue;
      ancestorsLevels.push({
        tag: '上级分类',
        label: `${ancestorName} 赋予的污染物限量要求`,
        isSelf: false,
        items: filtered
      });
    }
  }'''

NEW = '''      if (filtered.length === 0) continue;
      ancestorsLevels.push({
        tag: '上级分类',
        label: `${ancestorName} 赋予的污染物限量要求`,
        isSelf: false,
        items: filtered
      });
    }

    // v82-fix83: L3 节点 idx 空时, 额外显示「跨 L2 通类 row 段」。
    //   策略: 收集 a1l1=path[0], a1l2!=path[1], a1l3='', a1l4='' 的 row
    //   (即同 L1 章节下, 其他 L2 通类 row + L1 通类 row)
    //   排除 ancestorsLevels 段已显示的 row + 本级 primaryItems
    //   仅当 path.length === 3 且 primaryItems.length === 0 时显示
    if (path.length === 3 && primaryItems.length === 0) {
      const ownKey = dedupKey;  // 引用 dedupKey 函数
      const crossL2Items = (rawItems || items_all_for_lookups || [])
        .filter(x => {
          // 必须 a1l1 = path[0] (同 L1 章节)
          const xL1 = (x.a1_l1 || '').toString().replace(/[()（）\\[\\]【】:：,，.。、]/g, '').toLowerCase().trim();
          const pathL1 = path[0].replace(/[()（）\\[\\]【】:：,，.。、]/g, '').toLowerCase().trim();
          if (xL1 !== pathL1) return false;
          // 必须 a1l2 ≠ path[1] (跨 L2)
          const xL2 = (x.a1_l2 || '').toString();
          if (xL2 === path[1]) return false;
          // 必须 a1l3/l4 空 (L2/L1 通类 row, 非其他 L3/L4 own row)
          if (x.a1_l3 || x.a1_l4) return false;
          // 必须 a1l1 不空 (排除锡表空 row)
          if (!x.a1_l1) return false;
          return true;
        })
        .filter(x => !primKey.has(dedupKey(x)))
        .map(x => ({ ...x, _viaSub: '同章节其他通类' }));
      // 收集已显示的 ancestorsLevels dedupKey, 去重
      const shownKeys = new Set();
      for (const seg of ancestorsLevels) {
        for (const it of seg.items) shownKeys.add(dedupKey(it));
      }
      for (const it of crossL2Items) shownKeys.add(dedupKey(it));
      const crossFiltered = crossL2Items.filter(x => !shownKeys.has(dedupKey(x)) || !shownKeys.has(dedupKey(x)));
      if (crossFiltered.length > 0) {
        ancestorsLevels.push({
          tag: '跨级',
          label: '同章节其他通类赋予的污染物限量要求',
          isSelf: false,
          items: crossFiltered
        });
      }
    }
  }'''

if OLD not in html:
    print('OLD 块未找到, 终止')
    import sys; sys.exit(1)

count = html.count(OLD)
print(f'OLD 块匹配: {count} 处')

html_new = html.replace(OLD, NEW, 1)
with open(PATH, 'w', encoding='utf-8') as f:
    f.write(html_new)

print(f'已替换 1 处')
print(f'文件大小: {len(html)} → {len(html_new)}')
