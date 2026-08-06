"""build_all.py —— jianyu 数据单一事实源构建器 + 自动部署

依赖关系（上游 → 下游）：
  1. category_ids.json (人工维护)
  2. subcategory_ids.json (auto_slug 或人工维护)
  3. table_ids.json (auto-gen from gb_checklist_subcat.json)
  4. master.json (records 来自人工 ETL)
  5. gb_checklist_subcat.json (原始 PDF ETL 产物)
  6. subcat_to_items.json (人工维护 alias 表)

build_all.py 做的事：
  1. 从 source/records.json (or master.json) → 注入 id + *_id 字段
  2. 重建 master.json 索引（by_canonical / by_category / by_item）
  3. µ/μ 归一化
  4. enrich gb_checklist_subcat.json (注入 table_id)
  5. enrich subcat_to_items.json (注入 *_id)
  6. 同步 sw.js DATA_VERSION
  7. 跑 validate.py
  8. （可选）git commit + push 触发 GitHub Pages 自动部署

⚠️ 本脚本假设上游 JSON 已经存在；本脚本只做"派生产物生成 + 注入 id"
⚠️ 禁止手工修改生成物（master.json / gb_checklist_subcat.json 的 *_id 字段等）
   如发现错误，先修 source，再跑 build_all.py

用法：
  python scripts/build_all.py                # build + validate（不 push）
  python scripts/build_all.py --push         # build + validate + git push
  python scripts/build_all.py --push --yes   # 自动 confirm（不询问）
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))


def step(title):
    print(f'\n{"=" * 60}')
    print(f'  {title}')
    print(f'{"=" * 60}')


def run_script(name):
    """运行 scripts/<name>.py"""
    path = os.path.join(ROOT, 'scripts', name)
    if not os.path.exists(path):
        print(f'⚠️ scripts/{name} 不存在，跳过')
        return
    print(f'→ python scripts/{name}')
    r = subprocess.run([sys.executable, path], cwd=ROOT)
    if r.returncode != 0:
        print(f'❌ scripts/{name} 失败（exit {r.returncode}）')
        sys.exit(1)


def git(*args, check=True):
    """运行 git 命令"""
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f'❌ git {" ".join(args)} 失败')
        print(r.stderr)
        sys.exit(1)
    return r


def has_changes():
    """检查是否有未提交的修改"""
    r = git('status', '--porcelain', check=False)
    return bool(r.stdout.strip())


def get_master_meta():
    """读取 master.json 的 _meta"""
    p = os.path.join(ROOT, 'data/master.json')
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding='utf-8')).get('_meta', {})


def confirm(prompt):
    """询问用户确认"""
    if not sys.stdin.isatty():
        return False
    while True:
        ans = input(f'{prompt} [y/N] ').strip().lower()
        if ans in ('y', 'yes'):
            return True
        if ans in ('', 'n', 'no'):
            return False


def do_push(auto_yes=False):
    """git add + commit + push（GitHub Pages 自动部署）"""
    step('🚀 自动 commit + push')

    meta = get_master_meta()
    schema_version = meta.get('schema_version', '?')
    data_version = meta.get('data_version', '?')
    record_count = meta.get('record_count', len(meta.get('records', []))) if isinstance(meta.get('record_count'), int) else '?'

    print(f'   schema_version: {schema_version}')
    print(f'   data_version:   {data_version}')
    print(f'   record_count:   {record_count}')

    # 1. 检查是否有修改
    if not has_changes():
        print('ℹ️ 无文件改动，跳过 commit + push')
        return False

    # 2. 显示待提交文件
    r = git('status', '--short', check=False)
    print(f'\n待提交：\n{r.stdout}')

    # 3. 用户确认
    if not auto_yes and not confirm('确认 commit + push？'):
        print('⏭️ 用户取消，跳过 commit + push')
        return False

    # 4. git add -A
    git('add', '-A')

    # 5. commit
    msg = f'build: schema {schema_version} data_version {data_version}'
    git('commit', '-m', msg)
    print(f'✅ committed: {msg}')

    # 6. push
    r = subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'❌ git push 失败')
        print(r.stderr)
        sys.exit(1)
    print(f'✅ pushed to origin/main')
    print(f'   → GitHub Pages 将在 1-2 分钟内自动部署')
    return True


def main():
    parser = argparse.ArgumentParser(description='jianyu build_all')
    parser.add_argument('--push', action='store_true', help='build + validate 后自动 git commit + push')
    parser.add_argument('--yes', '-y', action='store_true', help='跳过用户确认（与 --push 配合）')
    args = parser.parse_args()

    print('🚀 jianyu build_all.py —— 单一事实源构建器\n')

    # 步骤顺序：先重建 ID 表（依赖源数据），再升级 master，最后 enrich 派生 JSON
    step('Step 1/6: 校验 category_ids.json（人工维护）')
    print('   ⚠️ category_ids.json 是上游事实源，需人工维护')
    if not os.path.exists(os.path.join(ROOT, 'data/category_ids.json')):
        print('   ❌ data/category_ids.json 不存在，请先人工创建')
        sys.exit(1)

    step('Step 2/6: 生成 subcategory_ids.json（master + GB 检验项目表）')
    run_script('gen_subcategory_ids.py')

    step('Step 3/6: 生成 table_ids.json（GB 检验项目表）')
    run_script('gen_table_ids.py')

    step('Step 4/6: 重建 master.json（加 id + 索引 + µ/μ 归一化 + sw.js 同步）')
    run_script('rebuild_index.py')

    step('Step 5/6: enrich 派生 JSON（gb_checklist_subcat / subcat_to_items）')
    run_script('enrich_gb_checklist.py')
    run_script('enrich_subcat_to_items.py')

    step('Step 6/6: 升级 master.json 到 schema v1.2（注入 *_id 字段）')
    run_script('upgrade_master_v12.py')

    # 最后跑 validate
    step('🔍 跑 validate.py')
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts/validate.py')], cwd=ROOT)
    if r.returncode != 0:
        print('\n❌ validate.py 失败，build 终止')
        sys.exit(1)

    print('\n' + '=' * 60)
    print('✅ build_all.py 完成')
    print('=' * 60)

    # 可选：自动 commit + push
    if args.push:
        do_push(auto_yes=args.yes)
    else:
        print('\n📦 手动推送（如需自动推送：python scripts/build_all.py --push）')
        print('   git add -A && git commit && git push origin main')
        print('   → GitHub Pages 自动部署')


if __name__ == '__main__':
    main()