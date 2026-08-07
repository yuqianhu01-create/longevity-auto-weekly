import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports.json"
CANDIDATES = DOCS / "staging" / "weekly-candidates.json"

MODULE_ORDER = [
    "academic-frontier",
    "industry-progress",
    "health-food-competitors",
    "food-ingredients",
    "ai-applications",
]

SOURCE_CREDIBILITY = {
    "pubmed": "primary",
    "crossref": "primary",
    "clinicaltrials-gov": "official",
    "arxiv": "secondary",
}

SOURCE_KIND = {
    "clinicaltrials-gov": "clinical-registry",
    "arxiv": "preprint",
    "pubmed": "research",
    "crossref": "research",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_date(value):
    if not value:
        return None
    text = str(value).replace("/", "-")
    for part in (text[:10], text[:7], text[:4]):
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                date = datetime.strptime(part, fmt).date()
                if fmt == "%Y-%m":
                    return date.replace(day=1)
                if fmt == "%Y":
                    return date.replace(month=1, day=1)
                return date
            except ValueError:
                continue
    return None


def iso_datetime(value):
    date = parse_date(value)
    if not date:
        return datetime.now(timezone.utc).isoformat()
    return datetime(date.year, date.month, date.day, tzinfo=timezone.utc).isoformat()


def item_key(item):
    ids = item.get("identifiers", {})
    value = ids.get("doi") or ids.get("pmid") or ids.get("nctId")
    value = value or item.get("url") or item.get("titleOriginal") or item.get("titleZh") or item.get("id")
    return str(value or "").strip().lower()


def infer_module(item):
    module = item.get("primaryModuleId") or (item.get("moduleIds") or ["academic-frontier"])[0]
    return module if module in MODULE_ORDER else "academic-frontier"


def evidence_for(item):
    text = " ".join([item.get("titleOriginal", ""), item.get("titleZh", ""), item.get("fact", "")]).lower()
    source = item.get("sourceId")
    if source == "clinicaltrials-gov":
        return {"stage": "human-intervention", "quality": "low"}
    if source == "arxiv":
        return {"stage": "computational", "quality": "low"}
    if re.search(r"\b(mouse|mice|rat|rats|murine|zebrafish|drosophila|animal)\b", text):
        return {"stage": "animal", "quality": "moderate"}
    if re.search(r"\b(cell|cells|in vitro|organoid|fibroblast|keratinocyte|endothelial)\b", text):
        return {"stage": "cell", "quality": "moderate"}
    if re.search(r"\b(trial|randomized|clinical|cohort|participant|patient|human|women|men|adult)\b", text):
        return {"stage": "human-observational", "quality": "moderate"}
    return {"stage": "unclassified", "quality": "low"}


def score_components(item, age_days):
    source = item.get("sourceId")
    credibility = {"pubmed": 8.8, "crossref": 8.2, "clinicaltrials-gov": 8.0, "arxiv": 6.8}.get(source, 6.5)
    recency_bonus = max(0, 2.0 - min(age_days, 30) / 15)
    module = infer_module(item)
    return {
        "strategicRelevance": round(8.8 if module in MODULE_ORDER else 7.0, 1),
        "credibility": round(min(9.5, credibility), 1),
        "novelty": round(min(9.5, 7.2 + recency_bonus), 1),
        "actionability": round(8.4 if module != "academic-frontier" else 7.6, 1),
    }


def weighted_score(item):
    c = item.get("scoreComponents", {})
    return (
        0.35 * float(c.get("strategicRelevance", 0))
        + 0.30 * float(c.get("credibility", 0))
        + 0.20 * float(c.get("novelty", 0))
        + 0.15 * float(c.get("actionability", 0))
    )


def source_name(item):
    return item.get("sourceId") or "source"


def title_for(item):
    return item.get("titleZh") or item.get("titleOriginal") or item.get("id") or "Untitled"


def key_signal(item):
    return f"{source_name(item)} 在 {str(item.get('publishedAt') or '')[:10]} 收录/发布：{title_for(item)}"


def significance_for(item):
    module = infer_module(item)
    title = title_for(item)
    if module == "academic-frontier":
        return f"从机制、模型和证据阶段判断其是否能转化为延衰指标、实验设计或证据缺口：{title}"
    if module == "industry-progress":
        return f"提取上市、监管、合作或商业化信号，判断其对国内转化和合规边界的影响：{title}"
    if module == "health-food-competitors":
        return f"更新企业/品牌池，记录产品、原料、功效宣称、证据与渠道动作：{title}"
    if module == "food-ingredients":
        return f"提取原料名称、剂量、规范、安全性和人体证据设计，判断是否值得进入原料库：{title}"
    if module == "ai-applications":
        return f"判断其属于AI产业平台、产品工具、访谈信号还是抗衰模型，并记录可复用能力：{title}"
    return f"提取可行动的信息：{title}"


def action_for(item):
    module = infer_module(item)
    if module == "academic-frontier":
        return "阅读原文摘要和方法，优先提取机制轴、模型类型、人体相关性和下一步验证缺口。"
    if module == "industry-progress":
        return "追踪原始公告、政策文本或注册信息，提取适用边界、日期和对产品策略的影响。"
    if module == "health-food-competitors":
        return "更新企业档案，记录品牌、产品、成分、功效宣称、证据等级和商业动作。"
    if module == "food-ingredients":
        return "整理原料名、适用人群、剂量、法规状态和证据设计，标注是否可进入后续深挖。"
    if module == "ai-applications":
        return "区分AI产业应用与AI抗衰研究，记录公司/平台、模型能力、访谈观点和可落地场景。"
    return "阅读原文并提取下一步动作。"


def promote(item, age_days):
    source = source_name(item)
    module = infer_module(item)
    url = item.get("url")
    published_at = iso_datetime(item.get("publishedAt"))
    return {
        "id": item.get("id"),
        "sourceId": source,
        "sourceKind": SOURCE_KIND.get(source, "public-source"),
        "moduleIds": [module],
        "primaryModuleId": module,
        "titleOriginal": item.get("titleOriginal") or title_for(item),
        "titleZh": title_for(item),
        "url": url,
        "publishedAt": published_at,
        "identifiers": item.get("identifiers", {}),
        "verified": True,
        "verificationMode": "automated_source_date_link_gate",
        "fact": item.get("fact") or key_signal(item),
        "evidence": evidence_for(item),
        "sourceAssessment": {
            "credibility": SOURCE_CREDIBILITY.get(source, "secondary"),
            "impact": "medium",
        },
        "scoreComponents": score_components(item, age_days),
        "significance": significance_for(item),
        "recommendedAction": action_for(item),
        "provenance": [
            {
                "sourceId": source,
                "url": url,
                "trust": "automated-trusted-source" if source in SOURCE_CREDIBILITY else "automated-source",
                "contentScope": "metadata-record",
                "checkedAt": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "tags": {
            "mechanisms": [],
            "ingredients": [],
            "competitors": [],
            "applicants": [],
            "statuses": ["自动发布", "待阅读"],
        },
        "relatedModuleIds": [],
    }


def week_label(date_obj):
    year, week, _ = date_obj.isocalendar()
    return f"{year}-W{week:02d}"


def week_issue(date_obj):
    _, week, _ = date_obj.isocalendar()
    return week


def calendar_week_period(date_obj):
    start = date_obj - timedelta(days=date_obj.weekday())
    end = start + timedelta(days=6)
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
    }


def select_candidates(candidates, now, windows, min_items):
    clean = []
    for candidate in candidates.get("records", []):
        date = parse_date(candidate.get("publishedAt"))
        if not candidate.get("url") or not title_for(candidate) or not date:
            continue
        clean.append((candidate, date))

    selected = []
    selected_window = windows[-1]
    for window in windows:
        cutoff = now.date() - timedelta(days=window)
        selected = [(item, date) for item, date in clean if date >= cutoff]
        selected_window = window
        if len(selected) >= min_items:
            break
    return selected, selected_window


def build_report(items, period, now, recency_window_days):
    week = week_label(now.date())
    issue = week_issue(now.date())
    report_id = f"{week}-auto-{now.strftime('%Y%m%d%H%M')}"
    grouped = defaultdict(list)
    for item in items:
        grouped[item["primaryModuleId"]].append(item)

    selected = []
    for module in MODULE_ORDER:
        selected.extend(sorted(grouped[module], key=weighted_score, reverse=True)[:8])
    selected = sorted(selected, key=lambda item: (MODULE_ORDER.index(item["primaryModuleId"]), -weighted_score(item), item["publishedAt"]))
    top_ids = [item["id"] for item in sorted(selected, key=weighted_score, reverse=True)[:10]]
    generated_at = now.isoformat()
    report = {
        "schemaVersion": 1,
        "week": week,
        "issue": issue,
        "issueLabel": f"第{issue}期",
        "status": "published",
        "period": period,
        "generatedAt": generated_at,
        "judgement": "自动采集、自动去重、自动分类和自动发布；读者只需浏览正式周报并提取有用信息。",
        "opportunities": [],
        "risks": [],
        "actions": [],
        "moduleOrder": MODULE_ORDER,
        "items": selected,
        "topItemIds": top_ids,
        "coverage": [
            {
                "sourceId": "automated-weekly-pipeline",
                "status": "ok",
                "attempts": 1,
                "checkedAt": generated_at,
                "itemCount": len(selected),
                "recordErrors": 0,
                "pageErrors": 0,
                "recencyWindowDays": recency_window_days,
            }
        ],
        "publishedAt": generated_at,
    }
    return {
        "entry": {
            "id": report_id,
            "week": week,
            "issue": issue,
            "issueLabel": f"第{issue}期",
            "status": "published",
            "path": f"published/{report_id}.json",
            "generatedAt": generated_at,
            "publishedAt": generated_at,
        },
        "report": report,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--min-items", type=int, default=8)
    parser.add_argument("--min-modules", type=int, default=3)
    parser.add_argument("--fallback-days", default="30,90")
    parser.add_argument("--replace-current-week", action="store_true")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    windows = [args.days] + [int(value.strip()) for value in args.fallback_days.split(",") if value.strip()]
    candidates = load_json(CANDIDATES, {"records": [], "period": {}})
    reports = load_json(REPORTS, {"schemaVersion": 1, "generatedAt": now.isoformat(), "reports": []})

    current_week = week_label(now.date())
    if args.replace_current_week:
        reports["reports"] = [
            wrapper for wrapper in reports.get("reports", [])
            if wrapper.get("entry", {}).get("week") != current_week
        ]

    selected, selected_window = select_candidates(candidates, now, windows, args.min_items)
    promoted = []
    local_seen = set()
    for candidate, date in selected:
        key = item_key(candidate)
        if not key or key in local_seen:
            continue
        local_seen.add(key)
        promoted.append(promote(candidate, (now.date() - date).days))

    if not promoted:
        print("ERROR: no publishable candidates passed automated source/date/link/module gates; refusing to publish an empty report.")
        sys.exit(1)

    module_count = len({item["primaryModuleId"] for item in promoted})
    if len(promoted) < args.min_items:
        print(f"ERROR: only {len(promoted)} unique publishable candidates after {selected_window}-day automated window; minimum is {args.min_items}.")
        sys.exit(1)
    if module_count < args.min_modules:
        print(f"ERROR: publishable candidates cover only {module_count} modules; minimum is {args.min_modules}.")
        sys.exit(1)

    period = calendar_week_period(now.date())
    wrapper = build_report(promoted, period, now, selected_window)
    reports.setdefault("reports", []).append(wrapper)
    reports["generatedAt"] = now.isoformat()
    write_json(REPORTS, reports)
    print(f"Published automated report {wrapper['entry']['id']} with {len(promoted)} items")


if __name__ == "__main__":
    main()
