import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_PATH = ROOT / "docs" / "reports.json"


MODULE_ORDER = [
    "academic-frontier",
    "industry-progress",
    "health-food-competitors",
    "food-ingredients",
    "ai-applications",
]


def refresh_report(report: dict) -> None:
    report["moduleOrder"] = MODULE_ORDER
    report["judgement"] = ""
    report["opportunities"] = []
    report["risks"] = []
    report["actions"] = []
    report["items"] = [
        item
        for item in report.get("items", [])
        if item.get("sourceId") != "weekly-structure-20260804"
        and "subsection" not in str(item.get("id", ""))
        and "shared-profile" not in str(item.get("id", ""))
    ]


def main() -> None:
    data = json.loads(REPORTS_PATH.read_text(encoding="utf-8"))
    for record in data.get("reports", []):
        report = record.get("report")
        if isinstance(report, dict):
            refresh_report(report)
    REPORTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
