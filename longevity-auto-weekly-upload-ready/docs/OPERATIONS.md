# 延衰技术周报自动化说明

## 周次与日期

周报使用 ISO 周编号：

- 2026/08/03 - 2026/08/09 = 2026-W32 = 第32期
- 2026/08/10 - 2026/08/16 = 2026-W33 = 第33期

GitHub Action 每次运行时会自动写入：

- `report.week`：例如 `2026-W32`
- `report.issue`：例如 `32`
- `report.issueLabel`：例如 `第32期`
- `report.period.from`：本周周一，例如 `2026-08-03`
- `report.period.to`：本周周日，例如 `2026-08-09`

这些字段由 `scripts/promote_candidates_to_report.py` 自动计算，不需要手动改。

## GitHub 上如何自动保存

主工作流是：

```text
.github/workflows/auto-publish-weekly.yml
```

它每周一自动运行，也可以手动触发：

```text
Actions -> auto-publish-weekly -> Run workflow
```

流程是：

```text
collect_weekly_candidates.py
-> build_search_plan.py
-> evaluate_search_plan.py
-> promote_candidates_to_report.py
-> assign_primary_modules.py
-> validate_reports.py
-> commit docs/reports.json
-> GitHub Pages 自动部署
```

也就是说，每周新一期会被追加进：

```text
docs/reports.json
```

网站的“以往周报”下拉框会自动读取 `docs/reports.json` 里的所有历史周报，不需要单独手动建页面。

## 是否需要新增 workflow

暂时不需要。现在已有三个 workflow：

- `auto-publish-weekly.yml`：自动搜索、筛选、写入正式周报、提交到 GitHub。
- `validate-weekly.yml`：检查 JSON、栏目、报告格式有没有坏。
- `collect-weekly-candidates.yml`：保留为候选池/搜索计划调试用，不是正式发布主流程。

正式跑周报用 `auto-publish-weekly.yml`。

## 自动发布保护

`promote_candidates_to_report.py` 已加保护：

- 候选为空：不发布
- 低于 8 条：不发布
- 覆盖栏目少于 3 个：不发布
- 同一期内重复链接/DOI/PMID/NCT：去重
- 每条只进入一个最合适栏目

这样可以避免“只有几条、全挤在一个栏目”的测试结果被当成正式周报。

## 本地预览

本地预览需要保持 PowerShell server 运行：

```powershell
cd "C:\Users\YUQIAN HU\OneDrive - National University of Singapore\Documents\agent\longevity-auto-weekly-local-preview"
python -m http.server 4174 --bind 127.0.0.1
```

然后打开：

```text
http://127.0.0.1:4174/longevity-auto-weekly/
```
