from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict
from typing import Any
from dataclasses import dataclass, field

import httpx

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PRIMARY_URL = "https://raw.githubusercontent.com/24msingh24/2024-YCombinator-All-Companies-Datasets/main"
SUPPLEMENT_URL = "https://raw.githubusercontent.com/nikshepg/YC-Startup-Directory/main/YC_companies.csv"


@dataclass
class Company:
    id: str
    name: str
    slug: str
    website: str
    one_liner: str
    long_description: str
    team_size: str
    batch: str
    status: str
    industries: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    region: str = ""
    founders: list[dict[str, str]] = field(default_factory=list)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _build_company_map(
    companies_rows: list[dict],
    industries_rows: list[dict],
    tags_rows: list[dict],
    regions_rows: list[dict],
    founders_rows: list[dict],
) -> dict[str, Company]:
    companies = {}
    for row in companies_rows:
        cid = row["id"]
        companies[cid] = Company(
            id=cid,
            name=row["name"],
            slug=row["slug"],
            website=row["website"],
            one_liner=row.get("oneLiner", ""),
            long_description=row.get("longDescription", ""),
            team_size=row.get("teamSize", ""),
            batch=row.get("batch", ""),
            status=row.get("status", ""),
        )
    for row in industries_rows:
        cid = row.get("id", "")
        if cid in companies:
            companies[cid].industries.append(row.get("industry", ""))
    for row in tags_rows:
        cid = row.get("id", "")
        if cid in companies:
            companies[cid].tags.append(row.get("tag", ""))
    for row in regions_rows:
        cid = row.get("id", "")
        if cid in companies:
            companies[cid].region = row.get("region", "")
    slug_map = {c.slug: c for c in companies.values()}
    for row in founders_rows:
        slug = row.get("company_slug", "")
        if slug in slug_map:
            slug_map[slug].founders.append({
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "current_title": row.get("current_title", ""),
            })
    return companies


def _merge_supplement(companies: dict[str, Company], supplement_path: Path) -> dict[str, Company]:
    seen_slugs = {c.slug for c in companies.values()}
    rows = _read_csv(supplement_path)
    for row in rows:
        name = row.get("Company Name", "").strip()
        batch_raw = row.get("Batch", "").strip()
        industry = row.get("Industry", "").strip()
        description = row.get("Description", "").strip()
        if not name:
            continue
        slug = name.lower().replace(" ", "-").replace(".", "")
        if slug in seen_slugs:
            continue
        batch_code = _batch_to_code(batch_raw)
        new_id = f"s_{slug}"
        companies[new_id] = Company(
            id=new_id,
            name=name,
            slug=slug,
            website="",
            one_liner=description,
            long_description="",
            team_size="",
            batch=batch_code,
            status="Active",
            industries=[industry] if industry else [],
        )
        seen_slugs.add(slug)
    return companies


def _batch_to_code(batch: str) -> str:
    mapping = {"winter": "W", "spring": "S", "summer": "S", "fall": "F"}
    parts = batch.strip().split()
    if len(parts) >= 2:
        season = parts[0].lower()
        year = parts[1]
        prefix = mapping.get(season, "S")
        if len(year) == 4:
            year = year[-2:]
        return f"{prefix}{year}"
    for s, code in mapping.items():
        if s in batch.lower():
            year = batch.lower().replace(s, "").strip()
            return f"{code}{year[-2:]}"
    return batch


def batch_year(batch: str) -> int | None:
    if not batch or len(batch) < 3:
        return None
    year_str = batch[1:]
    try:
        year = int(year_str)
        return year + 2000 if year < 100 else year
    except ValueError:
        return None


def load() -> dict[str, Company]:
    companies_path = DATA_DIR / "companies.csv"
    if not companies_path.exists():
        msg = "Dataset not found. Run `uv run yc refresh` to download it."
        raise FileNotFoundError(msg)
    companies_rows = _read_csv(companies_path)
    industries_rows = _read_csv(DATA_DIR / "industries.csv")
    tags_rows = _read_csv(DATA_DIR / "tags.csv")
    regions_rows = _read_csv(DATA_DIR / "regions.csv")
    founders_rows = _read_csv(DATA_DIR / "founders.csv")
    companies = _build_company_map(companies_rows, industries_rows, tags_rows, regions_rows, founders_rows)
    supplement_path = DATA_DIR / "supplement.csv"
    if supplement_path.exists():
        companies = _merge_supplement(companies, supplement_path)
    return companies


async def _download_csv(url: str, path: Path) -> None:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
    path.write_text(resp.text)


async def refresh() -> None:
    import asyncio
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tables = ["companies", "founders", "industries", "tags", "regions"]
    tasks = []
    for table in tables:
        url = f"{PRIMARY_URL}/{table}.csv"
        path = DATA_DIR / f"{table}.csv"
        tasks.append(_download_csv(url, path))
    tasks.append(_download_csv(SUPPLEMENT_URL, DATA_DIR / "supplement.csv"))
    await asyncio.gather(*tasks)


def stats(companies: dict[str, Company]) -> dict:
    total = len(companies)
    statuses: dict[str, int] = defaultdict(int)
    batches: dict[str, int] = defaultdict(int)
    years: dict[int, int] = defaultdict(int)
    industries: dict[str, int] = defaultdict(int)
    for c in companies.values():
        statuses[c.status] += 1
        batches[c.batch] += 1
        yr = batch_year(c.batch)
        if yr:
            years[yr] += 1
        for ind in c.industries:
            if ind:
                industries[ind] += 1
    return {
        "total": total,
        "statuses": dict(sorted(statuses.items(), key=lambda x: -x[1])),
        "batches": len(batches),
        "years": dict(sorted(years.items())),
        "industries": dict(sorted(industries.items(), key=lambda x: -x[1])),
    }
