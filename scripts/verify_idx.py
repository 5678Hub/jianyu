#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
验证 web app 的 idx 索引命中情况(模拟 gb2762.html 的 buildItemIndex 逻辑)。

用法:
  python3 scripts/verify_idx.py                 # 列出所有 L1 分类 idx 命中数
  python3 scripts/verify_idx.py L1 分类名        # 查看指定 L1 分类的 idx 详情
  python3 scripts/verify_idx.py --zero-l2        # 列出 idx 命中 0 的 L2 分类
  python3 scripts/verify_idx.py --path 路径      # 查看指定路径(用 / 分隔)的 idx 详情

实现: 完全模拟 gb2762.html buildItemIndex 逻辑,包括:
  - walkExact + Fallback B (item 按 a1_l1/l2/l3/l4 精确注册)
  - v31: L2 通类项 (a1_l3 空 + path.length===2) 的 foodHasL3 判定
  - v30: L2 通类项扩散到 L3 children idx
  - v36: 已被 v58 撤销 (L1 通类项不再扩散到 L2 children)
  - v23/v29: 兄弟节点探测 (path.length>=3)
  - v35: getExcludes + sibIsExcluded,row "除外"列表排除对应 sib

限制: 不模拟 v23 的副作用(如某些 row 因为 a1_l3 错位而触发兄弟节点探测)。

norm 必须用 re.sub(r'[,，、;；()（）\[\]【】:：\s]+', ...) 正则替换字符集合,
不能用 str.replace('()（）[]【】', '') — 后者只替换连续字符串,不会替换单个括号。
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


def sib_core(name):
    """模拟 gb2762.html 的 sibCore:删除从括号/方括号/花括号/全角括号开始到结尾"""
    return re.sub(r'[([{【（].*$', '', name).strip()


def get_excludes(food):
    """v35: 提取 row.food 中的 '除外' 列表(如 '新鲜藻类(螺旋藻除外)' -> ['螺旋藻'])"""
    m = (food or '').toString() if hasattr(food or '', 'toString') else str(food or '')
    m = re.search(r'[\(（]([^)）]+除外)[\)）]', m)
    if not m:
        return []
    exc_str = m.group(1).replace('除外', '')
    parts = re.split(r'[、,，及和\s]+', exc_str)
    return [norm(p) for p in parts if p and len(p) >= 2]


def sib_is_excluded(sib_name, excludes):
    if not excludes:
        return False
    sib_n = norm(sib_name)
    for exc in excludes:
        if sib_n == exc:
            return True
        if len(exc) >= 3 and (sib_n.startswith(exc) or exc.startswith(sib_n)):
            return True
    return False


def food_contains_sib(food, sib_core, sib_name):
    """v38: 检测 food 是否独立含 sibCore (边界字符判定)
    避免 '婴儿配方食品' 在 '特殊医学用途婴儿配方食品'/'较大婴儿配方食品'/'婴幼儿配方食品' 中误命中子串。
    """
    if not food or not sib_core:
        return False
    esc = re.escape(sib_core)
    if re.search(r'(^|[(【（\[[，,、\s])' + esc, food):
        return True
    if len(sib_core) >= 3 and sib_name:
        esc_name = re.escape(sib_name)
        if re.search(r'(^|[(【（\[[，,、\s])' + esc_name, food):
            return True
    return False


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
            if not matched and idx == len(a1_path) - 1 and len(target) >= 3 and n_name_norm.startswith(target):
                matched = True
            if not matched and idx >= 1:
                sib_core_n = sib_core(n['name'])
                sib_core_norm = norm(sib_core_n)
                if sib_core_norm == target and sib_core_n and len(n_name_norm) > len(target):
                    matched = True
            if matched:
                matched_here = True
                cur_path = path + [n['name']]
                if idx < len(a1_path) - 1 and n.get('children'):
                    walk(n['children'], cur_path, idx + 1)
                else:
                    paths.append(cur_path[:])
        if not matched_here and idx == len(a1_path) - 1 and path:
            paths.append(path[:])

    walk(tree_children, [], 0)
    return paths


def find_node_by_path(tree, path):
    cur = None
    for p in path:
        children = cur['children'] if cur else tree
        if not children:
            return None
        f = next((c for c in children if c['name'] == p), None)
        if not f:
            return None
        cur = f
    return cur


def build_idx():
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(TREE_JSON, 'r', encoding='utf-8') as f:
        tree = json.load(f)

    idx = collections.defaultdict(list)
    dup_keys = collections.defaultdict(set)

    def add_item(pk, it, c, dup_key):
        if dup_key in dup_keys[pk]:
            return
        dup_keys[pk].add(dup_key)
        idx[pk].append({**it, '_c': c['contaminant'], '_t': c['table_no']})

    tree_root = tree.get('children', tree)

    for c in data.get('contaminants', []):
        for it in c.get('items', []):
            a1_path = [it.get('a1_l1'), it.get('a1_l2'), it.get('a1_l3'), it.get('a1_l4')]
            a1_path = [x for x in a1_path if x]
            if not a1_path:
                continue

            dup_key = '%s|%s|%s|%s|%s|%s|%s' % (
                c['table_no'], it['food'], it.get('limit_value', ''), it.get('sub_value', ''),
                it.get('main_remark', ''), it.get('sub_remark', ''), it.get('note', ''))

            paths = walk_exact(tree_root, a1_path)

            for path in paths:
                pk = path_key(path)
                is_l2_cat = path.length == 2 if hasattr(path, 'length') else len(path) == 2
                is_l2_cat = is_l2_cat and not (it.get('a1_l3') or '').strip()

                # v31: L2 通类项 (a1_l3 空 + path.length===2) 的 foodHasL3 判定
                if is_l2_cat:
                    l2_node = find_node_by_path(tree_root, path)
                    if l2_node and l2_node.get('children'):
                        # v57: 即使 foodHasL3 也注册到 L2 本级 (PDF 表头 L2 通类项本身显示限量)
                        add_item(pk, it, c, dup_key)
                    else:
                        # L2 无 children → 注册到 L2 本级
                        add_item(pk, it, c, dup_key)
                else:
                    add_item(pk, it, c, dup_key)

                # v30 L2 通类项扩散 + v23/v29 兄弟节点探测
                spread_to_l3 = (len(path) >= 3 or is_l2_cat) and (it.get('food') or '')
                if spread_to_l3:
                    start_path = path[:-1] if not is_l2_cat else path
                    start_node = find_node_by_path(tree_root, start_path)
                    if start_node and start_node.get('children'):
                        current_leaf = None if is_l2_cat else path[-1]
                        excludes = get_excludes(it['food'])
                        for sib in start_node['children']:
                            if not is_l2_cat and sib['name'] == current_leaf:
                                continue
                            if not sib['name'] or len(sib['name']) < 2:
                                continue
                            if sib_is_excluded(sib['name'], excludes):
                                continue
                            sc = sib_core(sib['name'])
                            if not sc or len(sc) < 2:
                                continue
                            if food_contains_sib(it['food'], sc, sib['name']):
                                sib_path = start_path + [sib['name']]
                                sib_pk = path_key(sib_path)
                                add_item(sib_pk, it, c, dup_key)

                # v36 已被 v58 撤销: L1 通类项不再扩散到 L2 children
                # 原因: PDF 中 L1 通类项是"行表头",不应推到 L2 子页 (用户反馈)。
                #   副作用: L2 食糖/乳糖/淀粉糖 等"无自己 row 但 L1 通类项有"的 L2 子页会显示 0 命中,
                #   这是符合 PDF 的 (L2 本身无独立限量行,L1 通类项只在 L1 展示)。

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