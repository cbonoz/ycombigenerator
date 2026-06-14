from __future__ import annotations
import json
import os
import random
from pathlib import Path
from typing import Any

from opencode_sdk import OpencodeClient

from ycombigenerator.scraper import Company, batch_year
from ycombigenerator.analyzer import industry_trends, trending_topics

_DEFAULT_MODEL = "opencode-go/deepseek-v4-flash"


def _load_env() -> None:
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


_load_env()


def _client() -> OpencodeClient:
    if not os.environ.get("OPENCODE_API_KEY"):
        print("Usage: OPENCODE_API_KEY=your_key yc generate")
        raise RuntimeError("OPENCODE_API_KEY environment variable not set")
    try:
        return OpencodeClient()
    except Exception as e:
        raise RuntimeError(
            f"Cannot connect to opencode server: {e}\n"
            "Start it with: opencode serve"
        ) from e


def predict_trends(companies: dict[str, Company], top_n: int = 5) -> dict[str, list[dict[str, Any]]]:
    trends = industry_trends(companies, top_n=top_n)
    topics = trending_topics(companies, top_n=top_n)
    return {
        "growing_industries": [t for t in trends if t["trend"] == "growing"][:top_n],
        "emerging_tags": topics,
    }


def _build_context(companies: dict[str, Company], n_samples: int = 20) -> str:
    recent = [
        c for c in companies.values()
        if (batch_year(c.batch) or 0) >= 2023 and c.one_liner and c.industries
    ]
    sampled = random.sample(recent, min(n_samples, len(recent)))
    lines = []
    for c in sampled:
        inds = ", ".join(c.industries[:3])
        tags = ", ".join(c.tags[:3])
        line = f"- {c.name} ({c.batch}): {c.one_liner} | Industry: {inds}"
        if tags:
            line += f" | Tags: {tags}"
        lines.append(line)
    return "\n".join(lines)


def _build_trend_summary(companies: dict[str, Company]) -> str:
    trends = industry_trends(companies, top_n=5)
    topics = trending_topics(companies, top_n=5)
    lines = ["Growing industries:"]
    for t in trends:
        if t["trend"] == "growing":
            lines.append(f"  - {t['industry']} ({t['growth_pct']:+.0f}%)")
    lines.append("\nEmerging topics:")
    for t in topics[:5]:
        lines.append(f"  - {t['tag']} ({t['growth_pct']:+.0f}%)")
    return "\n".join(lines)


def _check_server() -> None:
    import urllib.request
    base = os.environ.get("OPENCODE_SERVER", "http://localhost:36000")
    try:
        urllib.request.urlopen(f"{base}/session", timeout=2)
    except Exception:
        raise RuntimeError(
            f"Cannot connect to opencode server at {base}.\n"
            "  Start it with:  opencode serve --port 36000\n"
            "  Or use template mode:  yc generate --template"
        )


def _fallback_generate() -> str:
    products = [
        "A platform", "An API", "A mobile app", "A marketplace", "A SaaS tool",
        "A collaboration hub", "An analytics dashboard", "A workflow automation",
        "A compliance tool", "A payment infrastructure", "A data pipeline",
        "An AI copilot", "A dev tool", "A no-code builder", "A vertical SaaS",
    ]
    benefits = [
        "simplifies", "automates", "accelerates", "democratizes", "secures",
        "optimizes", "streamlines", "unblocks", "decouples", "orchestrates",
    ]
    audiences = [
        "developers", "designers", "SMEs", "enterprise teams", "healthcare providers",
        "fintech companies", "remote workers", "data scientists", "sales teams",
        "HR departments", "supply chain managers", "creators", "legal professionals",
        "manufacturers", "educators",
    ]
    outcomes = [
        "ship faster", "reduce costs", "improve accuracy", "scale confidently",
        "comply with regulations", "collaborate in real-time", "make data-driven decisions",
        "automate repetitive work", "increase revenue", "delight their customers",
    ]
    solutions = [
        "code review", "document processing", "customer support", "inventory management",
        "fraud detection", "performance monitoring", "recruitment", "contract analysis",
        "supply chain visibility", "compliance tracking",
    ]
    platforms = [
        "all-in-one workspace", "low-code platform", "API marketplace", "knowledge base",
        "project management hub", "data integration platform", "analytics engine",
    ]
    actions = [
        "build faster", "deploy confidently", "collaborate seamlessly", "analyze deeply",
        "automate completely", "integrate easily", "scale globally",
    ]

    p = random.choice(products)
    ind = random.choice(["B2B", "B2B", "B2B", "Consumer", "Healthcare", "Fintech", "Developer Tools", "AI/ML"])
    aud = random.choice(audiences)
    ben = random.choice(benefits)
    out = random.choice(outcomes)
    sol = random.choice(solutions)

    name = "".join([aud.split()[0].title() if aud.split() else aud, ben.title()])

    one_liner = random.choice([
        f"{p} that {ben} {sol} for {aud}.",
        f"AI-powered {sol} that helps {aud} {out}.",
        f"The {random.choice(platforms)} for {aud} to {random.choice(actions)}.",
    ])

    why_now = random.choice([
        "Recent advances in LLMs make this feasible for the first time.",
        f"The shift to remote work has created an urgent need for better {sol}.",
        f"Regulatory pressure is forcing {aud} to adopt better tooling.",
        f"{aud.title()} are spending 40% of their time on manual {sol}.",
    ])

    founder_advice = random.choice([
        "Focus on one vertical and nail the workflow before expanding.",
        "YC recommends finding 5 design partners before writing code.",
        "Distribution will be your biggest challenge; start with outbound.",
        "The incumbents are slow-moving; use speed as your moat.",
    ])

    data = {
        "name": name,
        "one_liner": one_liner,
        "industry": ind,
        "problem": f"{aud.title()} struggle with {sol}. {why_now}",
        "why_now": why_now,
        "founder_advice": founder_advice,
    }
    return json.dumps(data)


def generate_company(companies: dict[str, Company], **kwargs: Any) -> str:
    use_fallback = kwargs.get("_fallback", False)
    if use_fallback:
        return _fallback_generate()

    _check_server()

    context = _build_context(companies)
    trend_summary = _build_trend_summary(companies)
    custom_prompt = kwargs.get("prompt", "")

    system_prompt = """You are a Y Combinator partner brainstorming the next batch of startups.
Generate a realistic, compelling YC startup idea. Be specific and concrete.
Output format:
{
  "name": "CompanyName",
  "one_liner": "A compelling one-sentence description",
  "industry": "industry category",
  "problem": "What problem it solves (2-3 sentences)",
  "why_now": "Why this is timely (1-2 sentences)",
  "founder_advice": "What YC would advise the founders (1 sentence)"
}"""

    user_prompt = f"""Here are recent YC companies for reference:
{context}

Current trends:
{trend_summary}
"""
    if custom_prompt:
        user_prompt += f"\nAdditional direction: {custom_prompt}"
    user_prompt += "\n\nGenerate a single realistic YC startup idea in JSON:"

    import httpx
    try:
        client = _client()
        session = client.create_session(title="yc-generator")
        resp = client.send_message(session["id"], f"{system_prompt}\n\n{user_prompt}")
    except httpx.TimeoutException:
        raise TimeoutError("LLM request timed out after 120 seconds")
    for p in resp.get("parts", []):
        if p.get("type") == "text" and p.get("text", "").strip():
            return p["text"]
    return ""


def generate_batch(companies: dict[str, Company], count: int = 5, **kwargs: Any) -> list[str]:
    return [generate_company(companies, **kwargs) for _ in range(count)]
