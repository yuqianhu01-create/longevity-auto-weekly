# 延衰技术情报周报维护说明

## 1. 竞品对象库

竞品名单维护在 `docs/watchlists/competitor-watchlist.json`。

本轮已按用户指定全部设为 A 级对象：

- 健食：汤臣倍健、万益蓝、完美、仙乐健康、同仁堂、东阿阿胶、健合。
- 女性健康：月神、BIOCARE、因贝森、斯维诗、安利、汤臣倍健、laife。
- 美妆：L'Oréal、Unilever、P&G/Olay/SK-II、ISDIN、爱茉莉太平洋。

特殊规则：

- 汤臣倍健只建一个企业档案，同时进入健食和女性健康分析。
- P&G -> Olay / SK-II 建立母子关系。
- 健合 -> 斯维诗建立母子关系。
- 爱茉莉太平洋按集团管理，重点护肤品牌在 90 天建库时核对。

## 2. 多板块怎么跑

运行顺序维护在 `docs/automation/run-plan.json`。

建议分四批：

1. 核心科学：`academic-frontier`、`ai-longevity`。
2. 商业与竞品：`industry-progress`、`health-food-competitors`、`womens-health-competitors`、`beauty-competitors`。
3. 应用与原料：`ai-applications`、`food-ingredients`。
4. 专利：`patent-radar`，只在专利凭据可用时运行。

缩窄搜索范围的原则：

- 竞品模块先跑对象库，不先跑宽泛行业词。
- 单对象用别名 + 模块关键词组合查询。
- 官方公司页、临床登记、监管页优先；专业媒体只做补充和交叉核验。
- 搜索失败写入 coverage，不解释为无动态。

## 3. 复用文献筛查 Markdown

把旧的文献筛查 `.md` 放入：

```bash
docs/staging/literature-md/
```

运行：

```bash
python scripts/import_literature_md.py
```

输出：

```bash
docs/staging/literature-md-candidates.json
```

这些记录默认是 `verified: false`，只能作为候选池。必须经过 DOI、PMID、原文页、发布日期、研究类型和证据阶段核验后，才能进入公开 `reports.json`。

## 4. Workflow

当前仓库没有源码构建链路，公开站点依赖 `docs/` 已构建文件，GitHub Pages 的 `pages-build-deployment` 会完成发布。

新增 workflow：

```bash
.github/workflows/validate-weekly.yml
```

它会在 push、PR 和手动触发时运行：

```bash
python scripts/validate_reports.py
```

这个 workflow 解决的是发布前数据质量门槛，不负责自动采集网页。后续如果要全自动周报，应新增独立采集 workflow，并让它只写 staging/review 数据；人工确认后再合并到 `docs/reports.json`。
