# 延衰技术情报周报

公开站点：<https://siyanpi.github.io/longevity-intelligence-weekly/>

面向延衰研发与科研转化的公开信息周报。每条内容区分已核实事实、证据判断、对延衰工作的意义和建议动作。

- [事实纠错](https://github.com/siyanpi/longevity-intelligence-weekly/issues/new/choose)
- [参与讨论](https://github.com/siyanpi/longevity-intelligence-weekly/discussions)

本站不构成医疗、投资、专利新颖性、侵权或自由实施法律意见。

## 本地维护入口

- 竞品对象库：`docs/watchlists/competitor-watchlist.json`
- 多板块运行顺序与搜索范围：`docs/automation/run-plan.json`
- 文献筛查 Markdown 暂存目录：`docs/staging/literature-md/`
- 导入文献筛查候选：`python scripts/import_literature_md.py`
- 校验公开报告、竞品对象库和运行计划：`python scripts/validate_reports.py`

当前仓库发布的是 `docs/` 下的静态站点产物，GitHub Pages 会通过内置 `pages-build-deployment` 发布。新增的 `.github/workflows/validate-weekly.yml` 负责在 push / PR / 手动触发时做数据校验，避免坏 JSON、漏模块、未核验条目或对象库关系错误直接进入公开站点。

更多流程说明见 `docs/OPERATIONS.md`。
