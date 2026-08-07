import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports.json"
WATCHLIST = DOCS / "watchlists" / "competitor-watchlist.json"
RUN_PLAN = DOCS / "automation" / "run-plan.json"
SOURCE_REGISTRY = DOCS / "automation" / "source-registry.json"


REQUIRED_MODULES = {
    "academic-frontier",
    "industry-progress",
    "health-food-competitors",
    "food-ingredients",
    "ai-applications",
}

LEGACY_MODULES = {
    "ai-longevity",
    "beauty-competitors",
    "womens-health-competitors",
    "patent-radar",
}

WATCHLIST_SUBGROUPS = {
    "womens-health-competitors",
    "beauty-competitors",
    "by-health-shared-profile",
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
            if module_id not in REQUIRED_MODULES and module_id not in LEGACY_MODULES:
                fail(f"unknown module in watchlist: {entity.get('id')} -> {module_id}")
        parent_id = entity.get("parentId")
        if parent_id and parent_id not in ids:
            fail(f"missing parent entity: {entity.get('id')} -> {parent_id}")
        for child_id in entity.get("children", []):
            if child_id not in ids:
                fail(f"missing child entity: {entity.get('id')} -> {child_id}")
    for module_id, module in data.get("modules", {}).items():
        if module_id not in REQUIRED_MODULES and module_id not in LEGACY_MODULES and module_id not in WATCHLIST_SUBGROUPS:
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
            if module_id not in REQUIRED_MODULES and module_id not in LEGACY_MODULES:
                fail(f"unknown module in run plan: {module_id}")
    registry_path = data.get("globalRules", {}).get("sourceRegistryPath")
    if registry_path and not (DOCS / registry_path.lstrip("/")).exists():
        fail(f"source registry does not exist: {registry_path}")


def validate_source_registry():
    data = load_json(SOURCE_REGISTRY)
    required = ["domesticLiteratureSources", "commercialObservationSources", "competitorSpecialSearch"]
    for key in required:
        if not data.get(key):
            fail(f"source registry missing {key}")


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
        source_keys = set()
        for item in report.get("items", []):
            if item.get("id") in item_ids:
                fail(f"duplicate item id in report: {item.get('id')}")
            item_ids.add(item.get("id"))
            module_ids = list(item.get("moduleIds", []))
            if not module_ids:
                fail(f"item has no modules: {item.get('id')}")
            if len(module_ids) != 1:
                fail(f"item must have exactly one display module: {item.get('id')} -> {module_ids}")
            primary_module = item.get("primaryModuleId")
            if primary_module and primary_module != module_ids[0]:
                fail(f"primaryModuleId does not match display module: {item.get('id')}")
            unknown = set(module_ids) - REQUIRED_MODULES - LEGACY_MODULES
            if unknown:
                fail(f"item has unknown modules: {item.get('id')} -> {sorted(unknown)}")
            source_key = item.get("url") or item.get("titleZh") or item.get("titleOriginal")
            if source_key in source_keys:
                fail(f"duplicate source/title in report: {item.get('id')} -> {source_key}")
            source_keys.add(source_key)
            if item.get("verified") is not True:
                fail(f"item is not verified: {item.get('id')}")
            if not item.get("url"):
                fail(f"item has no source url: {item.get('id')}")
            if not item.get("provenance"):
                fail(f"item has no provenance: {item.get('id')}")


def main():
    validate_watchlist()
    validate_run_plan()
    validate_source_registry()
    validate_reports()
    print("Reports, watchlist, source registry, and run plan passed validation.")


if __name__ == "__main__":
    main()
