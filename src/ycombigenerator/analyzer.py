from __future__ import annotations
import re
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


_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "it", "its", "that", "this",
    "these", "those", "we", "our", "you", "your", "they", "them", "their",
    "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "just", "about", "above", "after", "again", "against", "below",
    "between", "during", "before", "behind", "from", "into", "through",
    "up", "down", "out", "off", "over", "under", "made", "make", "making",
    "new", "one", "also", "like", "get", "use", "using", "used", "help",
    "helps", "helping", "platform", "built", "build", "building", "based",
    "via", "way", "well", "much", "many", "still", "yet",
}


def keyword_trends(companies: dict[str, Company], top_n: int = 12) -> list[dict[str, Any]]:
    years: dict[int, Counter] = defaultdict(Counter)
    for c in companies.values():
        yr = batch_year(c.batch)
        if yr is None or not c.one_liner:
            continue
        words = re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", c.one_liner.lower())
        for w in words:
            if w not in _STOP_WORDS:
                years[yr][w] += 1

    all_words: Counter = Counter()
    for yr_data in years.values():
        all_words.update(yr_data)
    top = [w for w, _ in all_words.most_common(50)]

    result = []
    for word in top:
        recent = sum(years[yr].get(word, 0) for yr in years if yr >= 2023)
        older = sum(years[yr].get(word, 0) for yr in years if yr < 2023)
        if recent == 0 and older == 0:
            continue
        growth = ((recent - older) / max(older, 1)) * 100
        series = [(yr, years[yr].get(word, 0)) for yr in sorted(years) if yr >= 2010]
        result.append({
            "keyword": word,
            "total": all_words[word],
            "growth_pct": round(growth, 1),
            "series": series,
        })

    result.sort(key=lambda x: -x["growth_pct"])
    return result[:top_n]


def batch_concentration(companies: dict[str, Company]) -> list[dict[str, Any]]:
    batches: dict[str, Counter] = defaultdict(Counter)
    for c in companies.values():
        if c.batch and c.industries:
            for ind in c.industries:
                batches[c.batch][ind] += 1

    result = []
    for batch, inds in sorted(batches.items(), key=lambda x: (batch_year(x[0]) or 0, x[0])):
        total = sum(inds.values())
        top_ind, top_count = inds.most_common(1)[0]
        top_share = top_count / total * 100
        result.append({
            "batch": batch,
            "year": batch_year(batch),
            "total": total,
            "top_industry": top_ind,
            "top_share": round(top_share, 1),
            "industry_count": len(inds),
        })
    return result
