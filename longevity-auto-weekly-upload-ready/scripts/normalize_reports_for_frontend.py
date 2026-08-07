import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_PATH = ROOT / "docs" / "reports.json"


DEFAULT_TAGS = {
    "mechanisms": [],
    "ingredients": [],
    "competitors": [],
    "applicants": [],
    "statuses": [],
}


def normalize_item(item: dict) -> None:
    tags = item.setdefault("tags", {})
    for key, value in DEFAULT_TAGS.items():
        tags.setdefault(key, list(value))
    item.setdefault("sourceAssessment", {"credibility": "secondary", "impact": "medium"})
    item.setdefault(
        "scoreComponents",
        {"strategicRelevance": 0, "credibility": 0, "novelty": 0, "actionability": 0},
    )
    item.setdefault("moduleIds", [])
    item.setdefault("provenance", [])
    item.setdefault("relatedModuleIds", [])
    item.setdefault("publishedAt", item.get("generatedAt"))
    item.setdefault("url", item.get("identifiers", {}).get("url", "#"))
    item.setdefault("titleOriginal", item.get("titleZh", item.get("id", "")))
    item.setdefault("titleZh", item.get("titleOriginal", item.get("id", "")))
    item.setdefault("fact", "")
    item.setdefault("significance", "")
    item.setdefault("recommendedAction", "")


def main() -> None:
    data = json.loads(REPORTS_PATH.read_text(encoding="utf-8"))
    for record in data.get("reports", []):
        report = record.get("report", {})
        for item in report.get("items", []):
            normalize_item(item)
    REPORTS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
