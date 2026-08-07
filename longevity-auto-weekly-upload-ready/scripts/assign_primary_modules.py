import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_PATH = ROOT / "docs" / "reports.json"
STATUS_PATH = ROOT / "docs" / "automation" / "module-fill-status.json"


MODULE_ORDER = [
    "academic-frontier",
    "industry-progress",
    "health-food-competitors",
    "food-ingredients",
    "ai-applications",
]

MIN_ITEMS_PER_MODULE = 5

MANUAL_PRIMARY_OVERRIDES = {
    "pubmed-sirt3-vascular-aging": "academic-frontier",
    "pubmed-brcars-heterochromatin": "academic-frontier",
    "pubmed-cadmium-ovarian-aging": "academic-frontier",
    "pubmed-cardiac-transcriptome-clock": "ai-applications",
    "pubmed-dha-brain-women": "food-ingredients",
    "pubmed-biological-age-muscle": "academic-frontier",
    "pubmed-ovary-single-cell-atlas": "academic-frontier",
    "frontiers-ai-neuroimaging-aging": "ai-applications",
    "pubmed-vitamin-c-serum": "health-food-competitors",
    "dovepress-fucoidan-bph-rct": "food-ingredients",
    "nct-smart-facial-coaching": "ai-applications",
    "nct-magnesium-sleep-women": "food-ingredients",
    "heights-menopause-mri-study": "health-food-competitors",
    "shiseido-cilantro-senolytic-skin": "health-food-competitors",
    "dsm-nous-koncentra": "industry-progress",
    "eggnovo-esm-novel-food": "industry-progress",
    "vitamin-world-womens-line": "health-food-competitors",
    "topgum-cognition-vision-gummies": "industry-progress",
    "hone-wthn-longevity-partnership": "industry-progress",
    "dcypher-john-lewis-ai-beauty": "ai-applications",
    "laneige-bespoke-amazon": "health-food-competitors",
}

REGULATORY_TERMS = {
    "政策", "法规", "监管", "注册", "批准", "授权", "备案", "指南", "合规", "新食品",
    "FDA", "NMPA", "EFSA", "regulatory", "regulation", "approval", "guidance", "compliance",
}
INDUSTRY_TERMS = {
    "推出", "上线", "合作", "商业化", "融资", "零售", "渠道", "平台", "市场", "供应链",
    "launch", "partnership", "commercial", "retail", "financing", "market",
}
COMPETITOR_TERMS = {
    "竞品", "企业", "品牌", "产品线", "美妆", "护肤", "女性", "更年期", "泌尿", "经期",
    "Shiseido", "LANEIGE", "DCYPHER", "Vitamin World", "Heights", "TopGum",
}
INGREDIENT_TERMS = {
    "原料", "成分", "提取物", "水解物", "DHA", "EPA", "镁", "岩藻多糖", "蛋壳膜",
    "猴头菇", "婆罗米", "叶黄素", "玉米黄质", "Koncentra", "ingredient", "botanical",
}
AI_TERMS = {
    "AI", "智能", "算法", "模型", "时钟", "转录组", "神经影像", "可穿戴", "个性化",
    "artificial intelligence", "machine learning", "clock", "model",
}
ACADEMIC_TERMS = {
    "研究", "综述", "图谱", "机制", "小鼠", "细胞", "队列", "横断面", "开发与外部验证",
    "衰老", "表观遗传", "线粒体", "clinical", "study", "trial",
}


def text_of(item: dict) -> str:
    tags = item.get("tags", {})
    values = [
        item.get("id"),
        item.get("titleZh"),
        item.get("titleOriginal"),
        item.get("fact"),
        item.get("significance"),
        item.get("recommendedAction"),
        item.get("url"),
        *(tags.get("mechanisms") or []),
        *(tags.get("ingredients") or []),
        *(tags.get("competitors") or []),
        *(tags.get("statuses") or []),
    ]
    return " ".join(str(value) for value in values if value).lower()


def has_any(text: str, terms: set[str]) -> bool:
    return any(term.lower() in text for term in terms)


def choose_module(item: dict) -> str:
    if item.get("id") in MANUAL_PRIMARY_OVERRIDES:
        return MANUAL_PRIMARY_OVERRIDES[item["id"]]
    text = text_of(item)
    existing = item.get("moduleIds") or []

    if (item.get("sourceId") or "").startswith(("pubmed", "frontiers", "dovepress")) and not has_any(text, {"AI", "智能", "算法"}):
        return "academic-frontier"
    if has_any(text, REGULATORY_TERMS):
        return "industry-progress"
    if has_any(text, AI_TERMS):
        if "ai-applications" in existing or has_any(text, {"ai", "智能", "算法", "模型", "时钟", "可穿戴", "个性化"}):
            return "ai-applications"
    if has_any(text, COMPETITOR_TERMS):
        return "health-food-competitors"
    if has_any(text, INGREDIENT_TERMS):
        return "food-ingredients"
    if has_any(text, INDUSTRY_TERMS):
        return "industry-progress"
    if has_any(text, ACADEMIC_TERMS):
        return "academic-frontier"
    return existing[0] if existing else "academic-frontier"


def normalize_report(report: dict) -> dict:
    counts = Counter()
    for item in report.get("items", []):
        original_modules = list(dict.fromkeys((item.get("moduleIds") or []) + (item.get("relatedModuleIds") or [])))
        primary = choose_module(item)
        if primary not in MODULE_ORDER:
            primary = original_modules[0] if original_modules else "academic-frontier"
        related = [module for module in original_modules if module != primary]
        item["primaryModuleId"] = primary
        item["moduleIds"] = [primary]
        item["relatedModuleIds"] = related
        counts[primary] += 1
    report["moduleOrder"] = MODULE_ORDER
    return {
        "week": report.get("week"),
        "itemCount": len(report.get("items", [])),
        "moduleCounts": {module: counts.get(module, 0) for module in MODULE_ORDER},
        "belowMinimum": {
            module: max(0, MIN_ITEMS_PER_MODULE - counts.get(module, 0))
            for module in MODULE_ORDER
            if counts.get(module, 0) < MIN_ITEMS_PER_MODULE
        },
    }


def main() -> None:
    data = json.loads(REPORTS_PATH.read_text(encoding="utf-8"))
    status = {
        "schemaVersion": 1,
        "updatedAt": "2026-08-04",
        "minimumUniqueItemsPerModule": MIN_ITEMS_PER_MODULE,
        "reports": [],
    }
    for wrapper in data.get("reports", []):
        report = wrapper.get("report", {})
        if isinstance(report, dict):
            status["reports"].append(normalize_report(report))
    REPORTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
