#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
验证 web app 的 idx 索引命中情况(模拟 gb2762.html 的 buildItemIndex 逻辑)。

用法:
  python3 scripts/verify_idx.py                 # 列出所有 L1 分类 idx 命中数
  python3 scripts/verify_idx.py L1 分类名        # 查看指定 L1 分类的 idx 详情
  python3 scripts/verify_idx.py --zero-l2        # 列出 idx 命中 0 的 L2 分类
  python3 scripts/verify_idx.py --path 路径      # 查看指定路径(用 / 分隔)的 idx 详情

注意: norm 必须用 re.sub(r'[,，、;；()（）\[\]【】:：\s]+', ...) 正则替换字符集合,
      不能用 str.replace('()（）[]【】', '') — 后者只替换连续字符串,不会替换单个括号。

限制: 本脚本只模拟了 walkExact + Fallback B(即 item 按 a1_l1/l2/l3/l4 精确注册的逻辑),
       **没有模拟 gb2762.html 的 v23/v29 兄弟节点探测 和 v30 L2 通类项扩散**。
       因此:
       - L1 / L2 级 idx 命中数是准确的(扩散只影响 L3,不改变 L1/L2 注册)
       - L3 级 idx 可能偏低(实际 web app 会通过 v30 把 L2 通类项推到匹配的 L3)
       如需验证 L3,请以浏览器实际显示为准。
"""
import json
import re
import collections
import sys
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JSON = os.path.join(BASE, 'data', 'gb2762', 'gb2762_2025.json')
TREE_JSON = os.path.join(BASE, 'data', 'gb2762', '_meta', 'official_a1_tree.json')


def norm(s):
    # 必须与 gb2762.html 的 pathKey 归一化一致:删除括号/逗号/顿号/冒号/空白
    return re.sub(r'[,，、;；()（）\[\]【】:：\s]+', '', (s or '').lower())


def path_key(path):
    return '|'.join(norm(p) for p in path)


def walk_exact(tree_children, a1_path):
    """模拟 gb2762.html matchItemToPaths 的 walkExact + Fallback B"""
    paths = []

    def walk(nodes, path, idx):
        if idx >= len(a1_path):
            return
        target = norm(a1_path[idx])
        matched_here = False
        for n in nodes:
            n_name_norm = norm(n['name'])
            matched = n_name_norm == target
            # 末层前缀匹配
            if not matched and idx == len(a1_path) - 1 and len(target) >= 3 and n_name_norm.startswith(target):
                matched = True
            # sibCore 匹配(去掉括号别名后的核心名)
            if not matched and idx >= 1:
                sib_core = re.sub(r'[([{【（].*$', '', n['name']).strip()
                sib_core_norm = norm(sib_core)
                if sib_core_norm == target and sib_core and len(n_name_norm) > len(target):
                    matched = True
            if matched:
                matched_here = True
                cur_path = path + [n['name']]
                if idx < len(a1_path) - 1 and n.get('children'):
                    walk(n['children'], cur_path, idx + 1)
                else:
                    paths.append(cur_path[:])
        # Fallback B: 走到 a1Path 末层但当前节点 children 为空 → 注册到 path 走的最远一层
        if not matched_here and idx == len(a1_path) - 1 and path:
            paths.append(path[:])

    walk(tree_children, [], 0)
    return paths


def build_idx():
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(TREE_JSON, 'r', encoding='utf-8') as f:
        tree = json.load(f)

    idx = collections.defaultdict(list)
    dup = collections.defaultdict(set)
    for c in data.get('contaminants', []):
        for it in c.get('items', []):
            a1_path = [it.get('a1_l1'), it.get('a1_l2'), it.get('a1_l3'), it.get('a1_l4')]
            a1_path = [x for x in a1_path if x]
            if not a1_path:
                continue
            for path in walk_exact(tree.get('children', tree), a1_path):
                pk = path_key(path)
                dk = '%s|%s|%s|%s' % (c['table_no'], it['food'], it.get('limit_value', ''), it.get('sub_value', ''))
                if dk in dup[pk]:
                    continue
                dup[pk].add(dk)
                idx[pk].append({**it, '_c': c['contaminant'], '_t': c['table_no']})
    return idx, tree


def display_count(item):
    """判断该 item 是否会在详情页显示(主列或副列有具体限量)"""
    has_main = (item.get('limit_value', '') or '').strip() not in ('', '—', '-')
    has_sub = (item.get('sub_value', '') or '').strip() not in ('', '—', '-')
    return has_main or has_sub


def main():
    idx, tree = build_idx()

    if len(sys.argv) > 1 and sys.argv[1] == '--zero-l2':
        print('=== L2 分类 idx 命中 0 ===')
        cnt = 0
        for n1 in tree.get('children', tree):
            for n2 in n1.get('children', []):
                pk = path_key([n1['name'], n2['name']])
                if len(idx[pk]) == 0:
                    cnt += 1
                    print('  %s > %s' % (n1['name'], n2['name']))
        print('总计 0 命中 L2: %d' % cnt)
        return

    if len(sys.argv) > 2 and sys.argv[1] == '--path':
        path = sys.argv[2].split('/')
        pk = path_key(path)
        print('=== idx 详情: %s ===' % ' > '.join(path))
        items = idx[pk]
        print('命中 %d,可显示 %d' % (len(items), sum(1 for i in items if display_count(i))))
        for it in items:
            print('  [表%s %s] food=%r lim=%s sub=%s note=%r (display=%s)' % (
                it['_t'], it['_c'], it['food'], it.get('limit_value', ''),
                it.get('sub_value', ''), it.get('note', ''), display_count(it)))
        return

    if len(sys.argv) > 1:
        name = sys.argv[1]
        pk = path_key([name])
        print('=== L1 分类 idx 详情: %s ===' % name)
        items = idx[pk]
        print('命中 %d,可显示 %d' % (len(items), sum(1 for i in items if display_count(i))))
        for it in items:
            print('  [表%s %s] food=%r lim=%s sub=%s note=%r (display=%s)' % (
                it['_t'], it['_c'], it['food'], it.get('limit_value', ''),
                it.get('sub_value', ''), it.get('note', ''), display_count(it)))
        return

    print('=== 所有 L1 分类 idx 命中数 ===')
    for n in tree.get('children', tree):
        pk = path_key([n['name']])
        items = idx[pk]
        disp = sum(1 for i in items if display_count(i))
        print('%-42s idx=%-3d display=%d' % (n['name'], len(items), disp))


if __name__ == '__main__':
    main()
