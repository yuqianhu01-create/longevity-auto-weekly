import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPORTS = DOCS / "reports.json"
WATCHLIST = DOCS / "watchlists" / "competitor-watchlist.json"
SOURCE_URL = "/longevity-intelligence-weekly/watchlists/competitor-watchlist.json"
ITEM_ID = "watchlist-a-level-competitors-20260803"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def entity_names(watchlist, module_id):
    ids = watchlist["modules"][module_id]["entities"]
    by_id = {entity["id"]: entity for entity in watchlist["entities"]}
    return [by_id[entity_id]["displayName"] for entity_id in ids]


def claim(claim_id, statement, field_paths, claim_type="verified_fact"):
    return {
        "claimId": claim_id,
        "type": claim_type,
        "statement": statement,
        "sourceIds": ["competitor-watchlist-20260803"],
        "fieldPaths": field_paths,
    }


def build_item(watchlist):
    health = "、".join(entity_names(watchlist, "health-food-competitors"))
    women = "、".join(entity_names(watchlist, "womens-health-competitors"))
    beauty = "、".join(entity_names(watchlist, "beauty-competitors"))
    return {
        "id": ITEM_ID,
        "sourceId": "competitor-watchlist-20260803",
        "sourceKind": "system",
        "moduleIds": [
            "health-food-competitors",
            "womens-health-competitors",
            "beauty-competitors",
        ],
        "titleOriginal": "A-level competitor watchlist and parent-child entity model",
        "titleZh": "A 级竞品对象库：健食、女性健康与美妆三条监控线合并建档",
        "url": SOURCE_URL,
        "publishedAt": "2026-08-03T00:00:00.000Z",
        "effectiveAt": "2026-08-03T00:00:00.000Z",
        "monitoredEntityId": "watchlist-system",
        "sourceObservationIds": ["obs-user-watchlist-20260803"],
        "collectionWindow": {
            "kind": "configuration",
            "start": "2026-08-03T00:00:00.000Z",
            "end": "2026-08-03T23:59:59.999Z",
        },
        "identifiers": {"url": SOURCE_URL},
        "verified": True,
        "fact": f"用户指定三类 A 级竞品对象：健食为{health}；女性健康为{women}；美妆为{beauty}。",
        "sourceAssessment": {"credibility": "user-specified", "impact": "high"},
        "scoreComponents": {
            "strategicRelevance": 9.8,
            "credibility": 9.0,
            "novelty": 8.8,
            "actionability": 9.6,
        },
        "significance": "监控范围从宽泛行业扫描收敛为实体优先情报：先查 A 级对象的公告、临床、法规、产品、AI 与专利线索，再补行业来源。",
        "recommendedAction": "后续每周先按对象库跑健食、女性健康和美妆竞品批次，并在 90 天基线中补齐别名、官网、核心产品、重点护肤品牌和历史证据。",
        "provenance": [
            {
                "sourceId": "competitor-watchlist-20260803",
                "url": SOURCE_URL,
                "trust": "trusted",
                "contentScope": "configuration-record",
                "publishedAt": "2026-08-03T00:00:00.000Z",
                "verified": True,
                "identifier": f"url:{SOURCE_URL}",
                "sourceRole": "primary",
                "original": True,
                "organizationFamily": "Longevity Intelligence Weekly",
                "contentFingerprint": "sha256:watchlist-user-specified-20260803",
            }
        ],
        "baselineComparison": "此前报告已有竞品模块，但缺少独立对象库与跨模块归并规则；本次新增 A 级对象、跨赛道复用、集团管理和母子关系字段。",
        "confirmedChange": "新增竞品对象库，汤臣倍健只建一个企业档案并进入健食与女性健康分析；P&G—Olay—SK-II、健合—斯维诗建立母子关系；爱茉莉太平洋按集团管理。",
        "whyItMatters": "对象库能显著缩窄搜索范围，减少宽泛行业查询带来的噪声和额度消耗，并保证同一企业在不同栏目中的结论不会互相打架。",
        "workImplications": [
            "每个 A 级对象建立唯一 entity_id、别名、模块归属、母子关系和 90 天基线，后续所有新闻、临床、法规、专利和产品记录都挂到同一个对象上。",
            "汤臣倍健跨健食与女性健康复用同一企业档案，避免重复建档；斯维诗和 Olay/SK-II 保留品牌级信号，但聚合到各自母公司下评估。"
        ],
        "positioningResponse": "优先用对象库驱动搜索：A 级对象官网/公告/产品/临床/监管来源为第一层，专业媒体为补充，宽泛行业搜索只用于发现非名单内强信号。",
        "evidenceGaps": [
            "部分中文品牌的英文名、官网域名、核心产品线和公司主体仍需在 90 天基线阶段核对。",
            "爱茉莉太平洋需在集团层管理，同时补充 LANEIGE、Sulwhasoo 等重点护肤品牌是否进入子品牌监控。"
        ],
        "recommendedActions": [
            "把 A 级对象库作为每周采集的第一批次输入，单对象限制查询数量，先查官方和监管来源。",
            "用 90 天建库补齐每个对象的官网、投资者关系页、新闻页、产品页、临床登记别名、专利申请人别名和重点 SKU。",
            "将文献筛查 md 导入 staging，只作为候选池；通过 DOI/PMID/原文页核验后再进入公开报告。"
        ],
        "companyClaims": [],
        "tags": {
            "mechanisms": ["竞品监控", "对象库", "母子关系"],
            "competitors": ["汤臣倍健", "万益蓝", "完美", "仙乐健康", "同仁堂", "东阿阿胶", "健合", "月神", "BIOCARE", "因贝森", "斯维诗", "安利", "laife", "L'Oréal", "Unilever", "P&G", "Olay", "SK-II", "ISDIN", "爱茉莉太平洋"],
            "statuses": ["A级对象", "配置已更新", "90天基线待补齐"]
        },
        "claimEvidence": [
            claim("watchlist-20260803-fact", f"用户指定三类 A 级竞品对象：健食为{health}；女性健康为{women}；美妆为{beauty}。", ["fact"]),
            claim("watchlist-20260803-change", "新增竞品对象库，汤臣倍健只建一个企业档案并进入健食与女性健康分析；P&G—Olay—SK-II、健合—斯维诗建立母子关系；爱茉莉太平洋按集团管理。", ["confirmedChange"]),
            claim("watchlist-20260803-action", "后续每周先按对象库跑健食、女性健康和美妆竞品批次，并在 90 天基线中补齐别名、官网、核心产品、重点护肤品牌和历史证据。", ["recommendedAction", "recommendedActions[0]"], "recommendation")
        ],
        "depth": "deep",
        "primaryModuleId": "health-food-competitors",
        "relatedModuleIds": ["womens-health-competitors", "beauty-competitors"],
        "priority": "high",
        "confidence": "high",
        "analysisDimensions": [
            {
                "dimensionId": "entityScope",
                "statement": "健食、女性健康、美妆分别建立 A 级对象列表，跨赛道企业共用同一档案。",
                "fieldPaths": ["fact"]
            },
            {
                "dimensionId": "parentChildModel",
                "statement": "P&G—Olay—SK-II、健合—斯维诗以母子关系管理，既保留品牌信号，也能回收到集团层判断。",
                "fieldPaths": ["confirmedChange"]
            },
            {
                "dimensionId": "runOrder",
                "statement": "竞品模块放在第二批次运行，在科学与 AI 基础证据之后、应用和专利之前，减少无关搜索。",
                "fieldPaths": ["recommendedActions[0]"]
            }
        ]
    }


def main():
    reports = load_json(REPORTS)
    watchlist = load_json(WATCHLIST)
    wrapper = reports["reports"][0]
    report = wrapper["report"]
    item = build_item(watchlist)

    report["items"] = [existing for existing in report["items"] if existing.get("id") != ITEM_ID]
    report["items"].insert(0, item)
    top_ids = [item_id for item_id in report.get("topItemIds", []) if item_id != ITEM_ID]
    report["topItemIds"] = [ITEM_ID] + top_ids[:9]
    if "health-food-competitors" not in report.get("moduleOrder", []):
        report.setdefault("moduleOrder", []).append("health-food-competitors")
    wrapper["entry"]["publishedAt"] = datetime.now(timezone.utc).isoformat()
    report["publishedAt"] = wrapper["entry"]["publishedAt"]

    REPORTS.write_text(json.dumps(reports, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Injected {ITEM_ID} into {REPORTS}")


if __name__ == "__main__":
    main()
