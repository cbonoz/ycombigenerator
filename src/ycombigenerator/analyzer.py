from __future__ import annotations
from collections import Counter, defaultdict
from typing import Any

from ycombigenerator.scraper import Company, batch_year


def industry_trends(companies: dict[str, Company], top_n: int = 15) -> list[dict[str, Any]]:
    years: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in companies.values():
        yr = batch_year(c.batch)
        if yr is None:
            continue
        for ind in c.industries:
            if ind:
                years[yr][ind] += 1
    all_industries: dict[str, int] = Counter()
    for yr_data in years.values():
        all_industries.update(yr_data)
    top = [ind for ind, _ in all_industries.most_common(top_n)]
    result = []
    for ind in top:
        series = [(yr, years[yr].get(ind, 0)) for yr in sorted(years) if yr >= 2015]
        if sum(v for _, v in series) == 0:
            continue
        recent = sum(v for yr, v in series if yr >= 2023)
        older = sum(v for yr, v in series if yr < 2023)
        growth = ((recent - older) / max(older, 1)) * 100
        result.append({
            "industry": ind,
            "total": all_industries[ind],
            "growth_pct": round(growth, 1),
            "trend": "growing" if growth > 20 else "declining" if growth < -20 else "stable",
            "series": series,
        })
    result.sort(key=lambda x: -x["growth_pct"])
    return result


def trending_topics(companies: dict[str, Company], top_n: int = 10) -> list[dict]:
    tags_past: Counter = Counter()
    tags_recent: Counter = Counter()
    for c in companies.values():
        yr = batch_year(c.batch)
        if yr is None:
            continue
        target = tags_recent if yr >= 2023 else tags_past
        for t in c.tags:
            if t:
                target[t] += 1
    result = []
    all_tags = set(tags_past) | set(tags_recent)
    for tag in all_tags:
        past = tags_past.get(tag, 0)
        recent = tags_recent.get(tag, 0)
        if past == 0 and recent == 0:
            continue
        growth = ((recent - past) / max(past, 1)) * 100
        result.append({
            "tag": tag,
            "past_count": past,
            "recent_count": recent,
            "growth_pct": round(growth, 1),
        })
    result.sort(key=lambda x: -x["growth_pct"])
    return result[:top_n]
