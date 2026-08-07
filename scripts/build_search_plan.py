import json
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
WATCHLIST = DOCS / "watchlists" / "competitor-watchlist.json"
SOURCE_REGISTRY = DOCS / "automation" / "source-registry.json"
OUTPUT = DOCS / "staging" / "search-plan.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def unique(values):
    seen = set()
    out = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def search_url(template: str, query: str) -> str:
    final_query = template.replace("{query}", query)
    return "https://www.bing.com/search?q=" + urllib.parse.quote(final_query)


def competitor_query(entity: dict, terms: list[str]) -> str:
    aliases = unique([entity.get("displayName"), *entity.get("aliases", [])])
    alias_expr = " OR ".join(f'"{alias}"' for alias in aliases)
    term_expr = " OR ".join(terms)
    return f"({alias_expr}) ({term_expr})"


def add_record(records: list[dict], **record) -> None:
    records.append({
            "reviewStatus": "pending",
            "publicationRule": "Automated publication is allowed only when URL, date, source, dedupe key, evidence stage, card type, and single best-fit module can be inferred.",
            "recencyPolicy": "Prefer items published or updated in the latest 14 days; expand to 30 or 90 days only when the module is below minimum and label the date clearly.",
            "qualityChecklist": [
                "clickable_url",
                "source_date",
                "single_best_fit_module",
                "one_sentence_key_signal_from_source",
                "automated_source_date_link_gate"
            ],
            **record,
        })


def add_source_records(records: list[dict], *, module_id: str, subgroup_id: str, subgroup_label: str, query: str, source_group: str, sources: list[dict], entity=None, card_type="evidence") -> None:
    for source in sources:
        add_record(
            records,
            id=f"{module_id}-{subgroup_id}-{entity.get('id') if entity else source['id']}-{source['id']}",
            moduleId=module_id,
            subgroupId=subgroup_id,
            subgroupLabel=subgroup_label,
            entityId=entity.get("id") if entity else "",
            entityName=entity.get("displayName") if entity else "",
            cardType=card_type,
            sourceGroup=source_group,
            sourceId=source["id"],
            sourceLabel=source["label"],
            mode=source.get("mode", "manual_review"),
            query=query,
            searchUrl=search_url(source["searchTemplate"], query),
        )


def main() -> None:
    watchlist = load_json(WATCHLIST)
    registry = load_json(SOURCE_REGISTRY)
    entity_by_id = {entity["id"]: entity for entity in watchlist["entities"]}
    competitor_terms = registry["competitorSpecialSearch"]["queryTerms"]

    records = []

    for subgroup_id, module in watchlist["modules"].items():
        if subgroup_id != "by-health-shared-profile" and not subgroup_id.endswith("-competitors"):
            continue
        for entity_id in module["entities"]:
            entity = entity_by_id[entity_id]
            query = competitor_query(entity, competitor_terms)
            add_source_records(
                records,
                module_id="health-food-competitors",
                subgroup_id=subgroup_id,
                subgroup_label=module["label"],
                query=query,
                source_group="commercial-observation",
                sources=registry.get("commercialObservationSources", []),
                entity=entity,
            )
            add_source_records(
                records,
                module_id="health-food-competitors",
                subgroup_id=subgroup_id,
                subgroup_label=module["label"],
                query=query,
                source_group="domestic-literature",
                sources=registry.get("domesticLiteratureSources", []),
                entity=entity,
            )
            add_record(
                records,
                id=f"health-food-competitors-{subgroup_id}-{entity_id}-official",
                moduleId="health-food-competitors",
                subgroupId=subgroup_id,
                subgroupLabel=module["label"],
                entityId=entity_id,
                entityName=entity["displayName"],
                cardType="evidence",
                sourceGroup="official-company",
                sourceId="official-company",
                sourceLabel="官网/官方公告/官方公众号",
                mode="manual_review",
                query=query,
                searchUrl="https://www.bing.com/search?q=" + urllib.parse.quote(query + " 官网 OR 官方 OR 公告 OR 投资者关系 OR 公众号"),
            )

    policy_queries = [
        "保健食品 原料 规范 注册 备案",
        "新食品原料 标准 规范 征求意见",
        "化妆品 功效 宣称 评价 监管",
        "健康食品 中草药 政策 监管 合规",
    ]
    for query in policy_queries:
        add_source_records(
            records,
            module_id="industry-progress",
            subgroup_id="policy-regulatory",
            subgroup_label="政策监管｜法规、注册与合规边界",
            query=query,
            source_group="domestic-government",
            sources=registry.get("domesticGovernmentSources", []),
        )

    ingredient_queries = [
        "中草药 保健食品 原料 人体试验 功效",
        "新食品原料 安全性 规格 剂量",
        "植物提取物 抗衰 皮肤 老化 人体证据",
    ]
    for query in ingredient_queries:
        add_source_records(
            records,
            module_id="food-ingredients",
            subgroup_id="evidence-design",
            subgroup_label="证据设计｜人体试验、功效宣称与剂量机制",
            query=query,
            source_group="domestic-literature",
            sources=registry.get("domesticLiteratureSources", []),
        )

    ai_queries = [
        "OpenAI Anthropic DeepMind AI biology drug discovery platform",
        "AI aging biological age model biomarker product",
        "OpenAI founder developer interview research platform",
        "Anthropic founder interview AI product commercialization",
        "NVIDIA AI biology healthcare aging",
    ]
    for query in ai_queries:
        add_source_records(
            records,
            module_id="ai-applications",
            subgroup_id="ai-industry",
            subgroup_label="AI产业应用｜研发平台、产品工具与商业化动作",
            query=query,
            source_group="ai-industry",
            sources=registry.get("aiIndustrySources", []),
        )

    for media_source in registry.get("mediaRecommendationSources", []):
        for query in media_source.get("queryTerms", []):
            add_record(
                records,
                id=f"recommendation-{media_source['id']}-{urllib.parse.quote(query, safe='')[:42]}",
                moduleId="ai-applications" if "AI" in query or "founder" in query else "academic-frontier",
                subgroupId="ai-industry" if "AI" in query or "founder" in query else "",
                subgroupLabel=media_source["label"],
                cardType="interview" if "interview" in query else "media",
                sourceGroup="media-recommendation",
                sourceId=media_source["id"],
                sourceLabel=media_source["label"],
                mode="manual_review",
                query=query,
                searchUrl="https://www.bing.com/search?q=" + urllib.parse.quote(query),
                requiredFields=["author_or_director_or_speaker", "country_or_region", "date", "focus_chapters_or_segments", "excerpt_or_key_moment", "inspiration", "clickable_url"],
            )

    payload = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "status": "staging_only",
        "scope": "competitor, domestic policy, domestic literature, AI industry, and media recommendation discovery tasks",
        "records": records,
        "nextStep": "GitHub Actions runs collect, ranking, dedupe, single-module assignment, and promote_candidates_to_report.py to write qualifying items into docs/reports.json automatically.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} search tasks into {OUTPUT}")


if __name__ == "__main__":
    main()
