import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs" / "staging" / "literature-md"
DEFAULT_OUTPUT = ROOT / "docs" / "staging" / "literature-md-candidates.json"


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
PMID_RE = re.compile(r"\bPMID[:\s]+(\d{6,})\b", re.I)
URL_RE = re.compile(r"https?://[^\s)>\]]+")


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def iter_sections(markdown):
    current_title = None
    buffer = []
    for line in markdown.splitlines():
        match = re.match(r"^(#{2,4})\s+(.+?)\s*$", line)
        if match:
            if current_title and buffer:
                yield current_title, "\n".join(buffer)
            current_title = clean(match.group(2).strip("* "))
            buffer = []
        elif current_title:
            buffer.append(line)
    if current_title and buffer:
        yield current_title, "\n".join(buffer)


def candidate_from_section(path, title, body):
    text = clean(body)
    doi = DOI_RE.search(text)
    pmid = PMID_RE.search(text)
    urls = URL_RE.findall(text)
    identifiers = {}
    if doi:
        identifiers["doi"] = doi.group(0).rstrip(".")
    if pmid:
        identifiers["pmid"] = pmid.group(1)
    if urls:
        identifiers["url"] = urls[0].rstrip(".,;")
    if not identifiers:
        return None
    return {
        "id": f"literature-md-{path.stem}-{abs(hash(title)) % 1000000}",
        "sourceKind": "research",
        "moduleIds": ["academic-frontier"],
        "titleOriginal": title,
        "titleZh": title,
        "url": identifiers.get("url")
        or (f"https://doi.org/{identifiers['doi']}" if "doi" in identifiers else f"https://pubmed.ncbi.nlm.nih.gov/{identifiers['pmid']}/"),
        "identifiers": identifiers,
        "verified": False,
        "fact": text[:280],
        "significance": "Imported from literature-screening Markdown; requires normal source verification before publication.",
        "recommendedAction": "Verify DOI/PMID, publication date, article type, population/model, and evidence stage before adding to a public report.",
        "tags": {
            "statuses": ["md-import", "pending-verification"]
        },
        "importedFrom": str(path.relative_to(ROOT)).replace("\\", "/")
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output = Path(args.output)
    records = []
    for path in sorted(input_dir.glob("*.md")):
        markdown = path.read_text(encoding="utf-8")
        for title, body in iter_sections(markdown):
            item = candidate_from_section(path, title, body)
            if item:
                records.append(item)

    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "staging_only",
        "records": records
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Imported {len(records)} literature candidates into {output}")


if __name__ == "__main__":
    main()
