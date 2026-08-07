import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_PLAN = ROOT / "docs" / "automation" / "run-plan.json"
RULES = ROOT / "docs" / "automation" / "classification-rules.json"
OUTPUT = ROOT / "docs" / "staging" / "weekly-candidates.json"
REQUEST_TIMEOUT = 12


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_json(url: str, timeout: int | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "longevity-auto-weekly/0.1"})
    with urllib.request.urlopen(req, timeout=timeout or REQUEST_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str, timeout: int | None = None) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "longevity-auto-weekly/0.1"})
    with urllib.request.urlopen(req, timeout=timeout or REQUEST_TIMEOUT) as response:
        return response.read().decode("utf-8", errors="replace")


def q(params: dict) -> str:
    return urllib.parse.urlencode(params, doseq=True, safe=':"/()')


def item_key(item: dict) -> str:
    identifiers = item.get("identifiers", {})
    return (
        identifiers.get("doi")
        or identifiers.get("pmid")
        or identifiers.get("nctId")
        or item.get("url")
        or item.get("titleOriginal")
        or item.get("id")
    ).lower()


def candidate(module_id: str, source_id: str, title: str, url: str, published_at: str, identifiers=None, snippet="") -> dict:
    safe_id = "".join(ch.lower() if ch.isalnum() else "-" for ch in f"{source_id}-{title[:70]}").strip("-")
    while "--" in safe_id:
        safe_id = safe_id.replace("--", "-")
    return {
        "id": safe_id[:96],
        "sourceId": source_id,
        "sourceKind": "candidate",
        "moduleIds": [module_id],
        "primaryModuleId": module_id,
        "titleOriginal": title,
        "titleZh": title,
        "url": url,
        "publishedAt": published_at,
        "identifiers": identifiers or {},
        "verified": False,
        "fact": snippet[:360],
        "significance": "Candidate from automated search; verify source, date, evidence stage, and module fit before publication.",
        "recommendedAction": "Promote automatically only after source/date/link/dedupe/module gates pass.",
        "tags": {"statuses": ["candidate", "pending-verification"]},
    }


def crossref_candidates(module_id: str, query: str, start: date, end: date, rows: int) -> list[dict]:
    params = {
        "query": query,
        "filter": f"from-pub-date:{start.isoformat()},until-pub-date:{end.isoformat()}",
        "rows": rows,
        "sort": "published",
        "order": "desc",
        "select": "DOI,title,URL,published-print,published-online,published",
    }
    url = "https://api.crossref.org/works?" + q(params)
    data = fetch_json(url)
    out = []
    for work in data.get("message", {}).get("items", []):
        titles = work.get("title") or []
        if not titles:
            continue
        published = work.get("published-online") or work.get("published-print") or work.get("published") or {}
        parts = (published.get("date-parts") or [[]])[0]
        published_at = "-".join(f"{part:02d}" if idx else str(part) for idx, part in enumerate(parts)) if parts else end.isoformat()
        doi = work.get("DOI")
        out.append(candidate(module_id, "crossref", titles[0], work.get("URL") or (f"https://doi.org/{doi}" if doi else ""), published_at, {"doi": doi} if doi else {}))
    return out


def pubmed_candidates(module_id: str, query: str, start: date, end: date, rows: int) -> list[dict]:
    esearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + q({
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": rows,
        "datetype": "pdat",
        "mindate": start.strftime("%Y/%m/%d"),
        "maxdate": end.strftime("%Y/%m/%d"),
        "sort": "pub+date",
    })
    ids = fetch_json(esearch).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    time.sleep(0.34)
    esummary = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + q({
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
    })
    data = fetch_json(esummary).get("result", {})
    out = []
    for pmid in ids:
        record = data.get(pmid, {})
        title = record.get("title")
        if not title:
            continue
        published_at = record.get("pubdate", end.isoformat()).replace(" ", "-")
        out.append(candidate(module_id, "pubmed", title, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", published_at, {"pmid": pmid}))
    return out


def clinicaltrials_candidates(module_id: str, query: str, rows: int) -> list[dict]:
    url = "https://clinicaltrials.gov/api/v2/studies?" + q({"query.term": query, "pageSize": rows, "format": "json"})
    data = fetch_json(url)
    out = []
    for study in data.get("studies", []):
        protocol = study.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        nct_id = ident.get("nctId")
        title = ident.get("briefTitle") or ident.get("officialTitle")
        if not nct_id or not title:
            continue
        published_at = (status.get("lastUpdatePostDateStruct") or status.get("studyFirstPostDateStruct") or {}).get("date", "")
        out.append(candidate(module_id, "clinicaltrials-gov", title, f"https://clinicaltrials.gov/study/{nct_id}", published_at, {"nctId": nct_id}))
    return out


def arxiv_candidates(module_id: str, query: str, rows: int) -> list[dict]:
    url = "https://export.arxiv.org/api/query?" + q({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": rows,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    text = fetch_text(url)
    root = ET.fromstring(text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", "", ns) or "").split())
        link = entry.findtext("atom:id", "", ns)
        published = entry.findtext("atom:published", "", ns)[:10]
        if title and link:
            out.append(candidate(module_id, "arxiv", title, link, published, {"arxivId": link.rsplit("/", 1)[-1]}))
    return out


SOURCE_RUNNERS = {
    "crossref": crossref_candidates,
    "pubmed": pubmed_candidates,
    "clinicaltrials": clinicaltrials_candidates,
    "arxiv": arxiv_candidates,
}


def build_queries(run_plan: dict) -> list[tuple[str, str, list[str]]]:
    module_terms = run_plan.get("searchNarrowing", {}).get("moduleTerms", {})
    buckets = []
    for batch in run_plan.get("batches", []):
        sources = [source for source in batch.get("preferredSources", []) if source in SOURCE_RUNNERS]
        for module_id in batch.get("moduleIds", []):
            terms = module_terms.get(module_id) or [batch.get("queryStrategy", module_id)]
            buckets.append([(module_id, term, sources) for term in terms])
    queries = []
    max_len = max((len(bucket) for bucket in buckets), default=0)
    for index in range(max_len):
        for bucket in buckets:
            if index < len(bucket):
                queries.append(bucket[index])
    return queries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--max-per-query", type=int, default=5)
    parser.add_argument("--query-limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()

    global REQUEST_TIMEOUT
    REQUEST_TIMEOUT = args.timeout

    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=args.days)
    run_plan = load_json(RUN_PLAN)
    rules = load_json(RULES)

    records = []
    errors = []
    seen = set()
    queries = build_queries(run_plan)
    if args.query_limit > 0:
        queries = queries[: args.query_limit]

    for module_id, query, sources in queries:
        for source_id in sources:
            try:
                runner = SOURCE_RUNNERS[source_id]
                if source_id in {"crossref", "pubmed"}:
                    found = runner(module_id, query, start, end, args.max_per_query)
                else:
                    found = runner(module_id, query, args.max_per_query)
                for item in found:
                    key = item_key(item)
                    if key and key not in seen:
                        seen.add(key)
                        records.append(item)
                time.sleep(0.25)
            except Exception as exc:
                errors.append({"moduleId": module_id, "sourceId": source_id, "query": query, "error": str(exc)})

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "staging_only",
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "minimumUniqueItemsPerModule": rules.get("minimumUniqueItemsPerModule", 5),
        "records": records,
        "errors": errors,
        "nextStep": "Run scripts/promote_candidates_to_report.py to automatically apply source/date/link/module gates and publish qualifying items to docs/reports.json.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Collected {len(records)} candidates with {len(errors)} source/query errors into {output}")
    if errors:
        print(json.dumps(errors[:10], ensure_ascii=False, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
