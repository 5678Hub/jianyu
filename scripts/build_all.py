"""build_all.py —— jianyu 数据单一事实源构建器

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

⚠️ 本脚本假设上游 JSON 已经存在；本脚本只做"派生产物生成 + 注入 id"
⚠️ 禁止手工修改生成物（master.json / gb_checklist_subcat.json 的 *_id 字段等）
   如发现错误，先修 source，再跑 build_all.py
"""
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


def main():
    print('🚀 jianyu build_all.py —— 单一事实源构建器\n')

    # 步骤顺序：先重建 ID 表（依赖源数据），再升级 master，最后 enrich 派生 JSON
    step('Step 1/6: 生成 category_ids.json（人工维护，本次跳过）')
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
    print('\n📦 现在可以：')
    print('   git add -A && git commit && git push origin main')
    print('   → GitHub Pages 自动部署')


if __name__ == '__main__':
    main()