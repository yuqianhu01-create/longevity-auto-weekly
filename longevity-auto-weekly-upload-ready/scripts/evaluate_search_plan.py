import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
RUN_PLAN = DOCS / "automation" / "run-plan.json"
SEARCH_PLAN = DOCS / "staging" / "search-plan.json"
WEEKLY_CANDIDATES = DOCS / "staging" / "weekly-candidates.json"
OUTPUT = DOCS / "staging" / "search-quality-report.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value):
    if not value:
        return None
    text = str(value)[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%b-%d", "%Y-%m"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def main():
    run_plan = load_json(RUN_PLAN, {})
    plan = load_json(SEARCH_PLAN, {"records": []})
    candidates = load_json(WEEKLY_CANDIDATES, {"records": []})
    records = plan.get("records", [])
    candidate_records = candidates.get("records", [])
    today = datetime.now(timezone.utc).date()
    window_days = int(run_plan.get("globalRules", {}).get("discoveryWindowDays", 14))

    dated_candidates = []
    stale_candidates = []
    for item in candidate_records:
        date = parse_date(item.get("publishedAt"))
        if date:
            dated_candidates.append(item)
            if (today - date).days > window_days:
                stale_candidates.append({
                    "id": item.get("id"),
                    "publishedAt": item.get("publishedAt"),
                    "ageDays": (today - date).days,
                    "title": item.get("titleZh") or item.get("titleOriginal"),
                    "url": item.get("url"),
                })

    missing_urls = [record.get("id") for record in records if not record.get("searchUrl")]
    by_source_group = Counter(record.get("sourceGroup", "unknown") for record in records)
    by_card_type = Counter(record.get("cardType", "evidence") for record in records)
    by_module = Counter(record.get("moduleId", "unknown") for record in records)

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "searchTaskCount": len(records),
        "candidateCount": len(candidate_records),
        "discoveryWindowDays": window_days,
        "searchPlanQuality": {
            "missingSearchUrls": missing_urls,
            "sourceGroupCounts": dict(sorted(by_source_group.items())),
            "cardTypeCounts": dict(sorted(by_card_type.items())),
            "moduleCounts": dict(sorted(by_module.items())),
        },
        "candidateRecency": {
            "datedCandidateCount": len(dated_candidates),
            "staleCandidateCount": len(stale_candidates),
            "staleCandidates": stale_candidates[:30],
        },
        "automatedPublicationRules": [
            "Publish only records with a clickable source URL, source ID, title, publication date, and dedupe key.",
            "Extract the key signal from the source record itself: fact, why it matters, and recommended action.",
            "Assign exactly one best-fit module; do not duplicate the same item across modules.",
            "Prefer the latest 14 days. Expand to 30 or 90 days only when a module has too few strong items.",
            "Readers only review the final website; no manual candidate queue is required."
        ],
        "websiteImportPath": [
            "GitHub Actions runs collect_weekly_candidates.py.",
            "GitHub Actions runs promote_candidates_to_report.py to write docs/reports.json.",
            "GitHub Actions runs assign_primary_modules.py and validate_reports.py.",
            "GitHub Actions commits docs/reports.json and staging reports back to main.",
            "GitHub Pages deploys the updated docs folder; the reader only opens the final website."
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote search quality report to {OUTPUT}")


if __name__ == "__main__":
    main()
