import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports.json"
WATCHLIST = DOCS / "watchlists" / "competitor-watchlist.json"
RUN_PLAN = DOCS / "automation" / "run-plan.json"


REQUIRED_MODULES = {
    "academic-frontier",
    "industry-progress",
    "ai-longevity",
    "ai-applications",
    "health-food-competitors",
    "beauty-competitors",
    "womens-health-competitors",
    "food-ingredients",
    "patent-radar",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_watchlist():
    data = load_json(WATCHLIST)
    entities = data.get("entities", [])
    ids = {entity.get("id") for entity in entities}
    if len(ids) != len(entities):
        fail("watchlist has duplicate or missing entity ids")
    for entity in entities:
        if entity.get("tier") != "A":
            fail(f"entity is not A-level: {entity.get('id')}")
        for module_id in entity.get("moduleIds", []):
            if module_id not in REQUIRED_MODULES:
                fail(f"unknown module in watchlist: {entity.get('id')} -> {module_id}")
        parent_id = entity.get("parentId")
        if parent_id and parent_id not in ids:
            fail(f"missing parent entity: {entity.get('id')} -> {parent_id}")
        for child_id in entity.get("children", []):
            if child_id not in ids:
                fail(f"missing child entity: {entity.get('id')} -> {child_id}")
    for module_id, module in data.get("modules", {}).items():
        if module_id not in REQUIRED_MODULES:
            fail(f"unknown watchlist module: {module_id}")
        for entity_id in module.get("entities", []):
            if entity_id not in ids:
                fail(f"module references missing entity: {module_id} -> {entity_id}")


def validate_run_plan():
    data = load_json(RUN_PLAN)
    ordered = [batch.get("order") for batch in data.get("batches", [])]
    if ordered != sorted(ordered):
        fail("automation batches are not ordered")
    for batch in data.get("batches", []):
        for module_id in batch.get("moduleIds", []):
            if module_id not in REQUIRED_MODULES:
                fail(f"unknown module in run plan: {module_id}")


def validate_reports():
    data = load_json(REPORTS)
    reports = data.get("reports", [])
    if not reports:
        fail("reports.json has no reports")
    for wrapper in reports:
        entry = wrapper.get("entry", {})
        report = wrapper.get("report", {})
        if entry.get("path") and not entry["path"].startswith("published/"):
            fail(f"entry path should stay under published/: {entry.get('id')}")
        module_order = report.get("moduleOrder", [])
        missing = REQUIRED_MODULES - set(module_order)
        if missing:
            fail(f"report missing required modules: {entry.get('id')} -> {sorted(missing)}")
        item_ids = set()
        for item in report.get("items", []):
            if item.get("id") in item_ids:
                fail(f"duplicate item id in report: {item.get('id')}")
            item_ids.add(item.get("id"))
            module_ids = set(item.get("moduleIds", []))
            if not module_ids:
                fail(f"item has no modules: {item.get('id')}")
            unknown = module_ids - REQUIRED_MODULES
            if unknown:
                fail(f"item has unknown modules: {item.get('id')} -> {sorted(unknown)}")
            if item.get("verified") is not True:
                fail(f"item is not verified: {item.get('id')}")
            if not item.get("url"):
                fail(f"item has no source url: {item.get('id')}")
            if not item.get("provenance"):
                fail(f"item has no provenance: {item.get('id')}")


def main():
    validate_watchlist()
    validate_run_plan()
    validate_reports()
    print("Reports, watchlist, and run plan passed validation.")


if __name__ == "__main__":
    main()
