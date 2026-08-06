# jianyu JSON 数据库 Schema 文档

> 生成时间：2026-08-06  
> 数据库版本：v1.0（统一 _meta 字段）  
> 在线地址：https://5678hub.github.io/jianyu/

## 总览

jianyu 是一个**纯前端**食品安全抽检风险查询工具，所有数据通过 `fetch()` 加载 JSON，无后端。

**数据加载顺序**（index.html `loadData()` 中并发加载）：

```
master.json                  ← 主库（712 条历史不合格记录）
category_map.json            ← 品名 → 大类-细类 映射
synonyms.json                ← 同义词规则
current_period/gb_checklist.json          ← 本期公告检验项目
categories_2026.json         ← 大类骨架（39 大类）
current_period/gb_checklist_subcat.json  ← 细类+检验项目（权威）
subcat_to_items.json         ← 别名 → 规范名 映射
```

## 通用约定

所有 JSON 顶层都有 `_meta` 字段（统一字段）：

```json
{
  "_meta": {
    "schema_version": "1.0",
    "last_updated": "2026-08-06 09:00:00+08:00",
    "encoding": "UTF-8",
    "bom": false,
    "source": "数据来源",
    "origin": "jianyu 食品安全抽检风险查询",
    "description": "文件用途简述"
  }
}
```

业务字段都在 `_meta` 之下，不使用 `_source / _note / _comment / _version` 这种散乱命名。

---

## 1. master.json（主库 · 核心）

**文件**：`data/master.json`  
**大小**：约 2.1 MB  
**记录数**：712 条（v3.3 校准版）

### 顶层结构

```json
{
  "_meta": { ... },
  "records": [Record, ...],          // 全部记录
  "by_canonical": { ... },           // 按规范食品名索引
  "by_category": { ... },            // 按大类索引
  "by_item": { ... },                // 按不合格项索引
  "project_weight": { ... }          // 项目权重（用于风险评分）
}
```

### Record 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `source` | str | 来源省份：`山东 / 辽宁 / 重庆` |
| `food_name_raw` | str | **原始食品名**（公告原文） |
| `food_name_canonical` | str | 规范食品名（按分类映射） |
| `big_category` | str | 大类（`蔬菜 / 水产品 / ...`） |
| `sub_category` | str | 细类（`"大类-细类"` 形式） |
| `category` | str | 大类全称（`食用农产品-水产品`） |
| `sampler_name` | str | 抽样单位（销售方） |
| `sampler_addr` | str | 抽样单位地址 |
| `prod_date` | str | 生产日期（`YYYY-MM-DD`） |
| `prod_name` | str | 标称生产单位（加工方） |
| `prod_addr` | str | 标称生产单位地址 |
| `fail_raw` | str | 原始不合格字符串 |
| `failed_items` | list[dict] | 不合格项明细（见下） |
| `bulletin_no` | str | 公告编号（`山东-2026-12期`） |

### failed_items 结构

```json
[
  {
    "item": "恩诺沙星",
    "result": "287µg/kg",
    "limit": "≤100µg/kg"
  }
]
```

> ⚠️ **重要**：limit 中的 `µ` (U+00B5 微符号) 与 `μ` (U+03BC 希腊字母) 在数据中**都可能存在**，前端 `normLimit()` 已统一。

### 索引结构

- `by_canonical[规范名]` → `{ records: [...], count: N, ... }`
- `by_category[大类]` → `{ records: [...], count: N, foods: set, ... }`
- `by_item[项目名]` → `{ records: [...], count: N, ... }`
- `project_weight[项目名]` → `{ weight: float, ... }`

---

## 2. categories_2026.json（大类骨架）

**文件**：`data/categories_2026.json`  
**大小**：约 4 KB  
**大类数**：39

### 顶层结构

```json
{
  "_meta": { ... },
  "categories": [
    { "no": "一", "name": "粮食加工品", "available": true },
    ...
  ]
}
```

### category 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `no` | str | 中文编号（一/二/...） |
| `name` | str | 大类名（**前端 key 用这个**） |
| `available` | bool | 前端是否展示 |

> 注意：`_full.json` 是**扩展版（含细类）**，但前端不引用，标记为 `legacy`。

---

## 3. current_period/gb_checklist_subcat.json（细类+检验项目 · 权威）

**文件**：`data/current_period/gb_checklist_subcat.json`  
**大小**：约 460 KB  
**大类数**：38  
**表数**：253（含跨大类续编表号）

### 顶层结构

```json
{
  "_meta": {
    "schema_version": "1.0",
    "category_count": 38,
    "table_count": 253,
    ...
  },
  "categories": {
    "水产品": [
      { "name": "淡水鱼", "table_no": "表35-1", "table_name": "淡水鱼", "items": [...], "notes": [] },
      ...
    ],
    ...
  }
}
```

### table 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | str | 细类名 |
| `table_no` | str | 表号（`表35-1`，含前缀） |
| `table_name` | str | 表名（与 name 通常相同） |
| `items` | list[dict] | 检验项目 |
| `notes` | list | 备注 |

### item 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `序号` | int | 项目编号 |
| `检验项目` | str | 项目名 |
| `依据法律法规或标准` | str | 依据 |
| `检测方法` | str | 检测方法（GB 5009.xx 等） |

> ⚠️ 表号 `33-44 / 33-8` 等**跨大类续编**是 PDF 原文真实编号，不能改成 `35-4`。

---

## 4. category_map.json（品名 → 分类）

**文件**：`data/category_map.json`  
**大小**：约 17 KB  
**类别数**：110  
**别名总数**：620

### 顶层结构

```json
{
  "_meta": { ... },
  "食用农产品-蔬菜": ["韭菜", "白菜", ...],
  "食用农产品-水产品": ["牛蛙", "鲤鱼", ...],
  ...
}
```

**key 格式**：`"大类全称-细类"`（如 `食用农产品-蔬菜`）  
**value**：食品名/别名 list

---

## 5. subcat_to_items.json（别名 → 规范名）

**文件**：`data/subcat_to_items.json`  
**大小**：约 107 KB  
**别名数**：847

### 顶层结构

```json
{
  "_meta": { ... },
  "aliases": {
    "乌鱼": "乌鳢",
    "黑鱼（淡水鱼）": "黑鱼",
    ...
  }
}
```

> ⚠️ **文件名易误导**：实际是品名别名 → 规范名映射，**不是**细类 → 检验项目映射（前端从未用作后者）。

---

## 6. synonyms.json（同义词规则集）

**文件**：`data/synonyms.json`  
**大小**：约 7 KB  
**规则数**：77

### 顶层结构

```json
{
  "_meta": {
    "principles": [
      "1. 把括号内的学名/别名作为 key 映射到主名",
      "2. 优先用 raw 名称显示",
      ...
    ]
  },
  "rules": [
    { "pattern": "...", "replacement": "...", "reason": "..." },
    ...
  ]
}
```

---

## 7. current_period/gb_checklist.json（本期公告）

**文件**：`data/current_period/gb_checklist.json`  
**大小**：约 8 KB  
**来源**：2026 年第 8 期某地市场监督管理局抽检公告附件 1

### 顶层结构

```json
{
  "_meta": {
    "period": "2026年第8期",
    "source": "（2026年第8期）.doc（本期公告）",
    "note": "本期公告检验项目（参考性；2026 抽检细则 PDF 已更细）",
    "category_count": 13
  },
  "categories": { ... }
}
```

> 此文件是本期公告原始检验项目；细颗粒度以 `gb_checklist_subcat.json` 为准。

---

## 8. categories_subcat.json（已 superseded · 建议删除）

**文件**：`data/categories_subcat.json`  
**状态**：`superseded`  
**取代文件**：`current_period/gb_checklist_subcat.json`

内容与 `gb_checklist_subcat.json` 重复，是 PDF 解析的早期版本。前端不使用，**建议删除**。

---

## 9. categories_2026_full.json（已 legacy · 建议删除）

**文件**：`data/categories_2026_full.json`  
**状态**：`legacy`  
**大小**：约 12 KB

大类 + 细类 展开版（含 subcategories），但前端从未引用此文件。  
前端实际使用：
- 大类骨架：`categories_2026.json`
- 细类+项目：`gb_checklist_subcat.json`

**建议删除**（或保留作历史参考）。

---

## 临时/中间文件（_开头）

这些是**校准过程中的中间产物**，不在交付物中：

- `_category_increment_v2.json` — 增量校准数据
- `_heuristic_suggestions.json` — 启发式建议
- `_quality_report.json` — 质量报告
- `_records_raw.json` / `_records_raw_v2_batch.json` — 原始记录
- `_doc_xinzhou8_full.txt` — 原始文档

> 这些文件**不打包**给 ChatGPT，仅作本地留档。

---

## 给 ChatGPT 的审查建议

如果做架构审查，关注：

1. **数据冗余**：master.json 中 records + 4 个索引占空间，是否应该用 IndexedDB？
2. **数据一致性**：by_canonical 等索引是否需要更新脚本（如新增记录时自动重建）？
3. **分类命名**：big_category 与 category 两个字段重复，是否可合并？
4. **跨类表号**：33-44 / 33-8 这种 PDF 跨大类续编，对前端展示逻辑有何影响？
5. **Unicode 字符**：limit 中 µ/μ 统一处理是否应移到数据预处理而非运行时？

---

## schema v1.2 升级说明（2026-08-06）

按 ChatGPT 审查建议实施的核心改造：

### 新增 ID 体系（程序内部稳定标识）

| 文件 | 内容 | 条数 |
|------|------|------|
| `data/category_ids.json` | 31 大类英文 slug ID + 中文名映射 | 40（1 root + 39） |
| `data/subcategory_ids.json` | 282 细类英文 slug ID（master 153 + GB 检验 129） | 282 |
| `data/table_ids.json` | 253 张检验项目表稳定 ID + continuation_of 续编关系 | 253 |

**ID 命名规则**：
- 大类：`snake_case` 英文短语，避免与同义词根冲突（如 `aquatic_products` ≠ `aquatic_products_processed`）
- 细类：`{big_id}-{sub_slug}`（slug 优先手工指定，未指定用 pypinyin 全拼自动生成）
- 表号：`gb2026-{big_id}-{norm_no}[-{sub_slug}]`（跨大类续编加 sub_slug 区分）

### master.json schema v1.1 → v1.2

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | str | record_id（r0001~rXXXX），全局唯一 |
| `big_category_id` | str | 大类英文 slug ID |
| `subcategory_id` | str | 细类英文 slug ID |
| `big_category` | str | **[deprecated]** 大类中文名 |
| `sub_category` | str | **[deprecated]** "大类-细类"中文拼接 |
| `category` | str | **[deprecated]** 大类全称 |

### failed_items[*] schema

| 字段 | 类型 | 说明 |
|------|------|------|
| `item` | str | 检验项目 |
| `result` | str | 实测值 |
| `limit` | str | 限值（已 µ/μ 归一化） |
| `limit_raw` | str | 原始 limit（仅不一致时存在） |
| `limit_normalized` | str | 归一化 limit（必填） |
| `result_normalized` | str | 归一化 result（必填） |
| `big_category_id` | str | 大类 ID |
| `subcategory_id` | str | 细类 ID |
| `table_id` | str \| null | 表号 ID（数据源无表号时 null） |

### 索引去重（schema v1.1）

| 字段 | 类型 | 说明 |
|------|------|------|
| `indexes.by_canonical[k]` | `{ids: [...], count, big_categories, food_names}` | 仅存 record_id 引用 |
| `indexes.by_category[k]` | `{ids: [...], count, foods, items}` | 同上 |
| `indexes.by_item[k]` | `{ids: [...], count, foods, big_categories}` | 同上 |

**效果**：master.json 体积 3.0 MB → 1.07 MB（-64%）

### 单一事实源流程（build_all.py）

```
上游事实源
├─ data/category_ids.json (人工维护)
├─ data/gb_checklist_subcat.json (PDF ETL 产物)
├─ data/subcat_to_items.json (人工维护 alias)
└─ data/master.json (records 来自手工 ETL)

build_all.py 一键执行：
  Step 1: 校验 category_ids.json
  Step 2: gen_subcategory_ids.py → 282 条 slug
  Step 3: gen_table_ids.py → 253 条 stable id
  Step 4: rebuild_index.py → master.json 加 id + 索引 + µ/μ + sw.js 同步
  Step 5: enrich_gb_checklist.py + enrich_subcat_to_items.py → 派生 JSON 注入 *_id
  Step 6: upgrade_master_v12.py → master.json 注入 *_id
  校验：validate.py
```

### Service Worker 缓存隔离

`sw.js` 顶部 `DATA_VERSION` 由 `rebuild_index.py` 自动同步，CACHE 名 = `jianyu-cache-${DATA_VERSION}`。
数据版本变了，activate 时清理所有旧缓存。

### 已确认不做的项（留给未来）

- IndexedDB 改造（当前 712 条规模不需要）
- category/subcategory 字段合并（ChatGPT 建议的"语义化合并"暂不需要；用 *_id 体系替代）