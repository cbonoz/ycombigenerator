from __future__ import annotations
import asyncio
import json
import os

import typer
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

app = typer.Typer(name="yc", help="Y Combinator company analyzer & generator")
console = Console()


@app.command()
def refresh():
    """Download the latest YC company dataset."""
    from ycombigenerator.scraper import refresh as _refresh
    with console.status("Downloading dataset..."):
        asyncio.run(_refresh())
    console.print("[green]Dataset refreshed successfully![/green]")


@app.command()
def stats():
    """Show dataset statistics."""
    from ycombigenerator.scraper import load, stats as _stats
    companies = load()
    s = _stats(companies)

    console.print(f"\n[bold]Total companies:[/bold] {s['total']}")
    console.print(f"[bold]Unique batches:[/bold] {s['batches']}")

    table = Table(title="Status Distribution")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")
    for status, count in s["statuses"].items():
        table.add_row(status, str(count))
    console.print(table)

    yr_table = Table(title="Companies by Year")
    yr_table.add_column("Year", style="cyan")
    yr_table.add_column("Count", justify="right")
    for year, count in list(s["years"].items())[-15:]:
        yr_table.add_row(str(year), str(count))
    console.print(yr_table)

    ind_table = Table(title="Top Industries")
    ind_table.add_column("Industry", style="cyan")
    ind_table.add_column("Count", justify="right")
    for ind, count in list(s["industries"].items())[:15]:
        ind_table.add_row(ind, str(count))
    console.print(ind_table)


@app.command()
def analyze():
    """Analyze YC company trends by industry and topic."""
    from ycombigenerator.scraper import load
    from ycombigenerator.analyzer import industry_trends, trending_topics
    companies = load()

    trends = industry_trends(companies, top_n=10)
    table = Table(title="Industry Trends (Growth % since 2023)")
    table.add_column("Industry", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Growth %", justify="right")
    table.add_column("Trend")
    for t in trends:
        table.add_row(t["industry"], str(t["total"]), f"{t['growth_pct']:+.0f}%", t["trend"])
    console.print(table)

    topics = trending_topics(companies, top_n=10)
    top_table = Table(title="Trending Topics")
    top_table.add_column("Tag", style="cyan")
    top_table.add_column("Past", justify="right")
    top_table.add_column("Recent", justify="right")
    top_table.add_column("Growth %", justify="right")
    for t in topics:
        top_table.add_row(t["tag"], str(t["past_count"]), str(t["recent_count"]), f"{t['growth_pct']:+.0f}%")
    console.print(top_table)


@app.command()
def trends():
    """Predict the next YC trends."""
    from ycombigenerator.scraper import load
    from ycombigenerator.generator import predict_trends as _predict
    companies = load()
    result = _predict(companies)
    console.print("[bold]Growing Industries[/bold]")
    for t in result["growing_industries"]:
        console.print(f"  [cyan]{t['industry']}[/cyan]: +{t['growth_pct']:.0f}%")
    console.print("\n[bold]Emerging Topics[/bold]")
    for t in result["emerging_tags"]:
        console.print(f"  [cyan]{t['tag']}[/cyan]: +{t['growth_pct']:.0f}%")


@app.command()
def generate(
    count: int = typer.Option(1, "--count", "-n", help="Number of ideas to generate"),
    prompt: str = typer.Option("", "--prompt", "-p", help="Custom prompt direction"),
    template: bool = typer.Option(False, "--template", "-t", help="Use template generator (no server needed)"),
    raw: bool = typer.Option(False, "--raw", help="Output raw JSON instead of formatted"),
):
    """Generate hypothetical YC startup ideas."""
    from ycombigenerator.scraper import load
    from ycombigenerator.generator import generate_company, generate_batch
    companies = load()

    with console.status("Generating startup idea..."):
        if count == 1:
            results = [generate_company(companies, prompt=prompt, _fallback=template)]
        else:
            results = generate_batch(companies, count=count, prompt=prompt, _fallback=template)

    for i, result in enumerate(results, 1):
        if raw:
            console.print(result)
        else:
            try:
                data = json.loads(result)
                console.print(f"\n[bold cyan]#{i}: {data.get('name', 'Untitled')}[/bold cyan]")
                console.print(f"  [italic]{data.get('one_liner', '')}[/italic]")
                console.print(f"  Industry: {data.get('industry', 'N/A')}")
                if data.get("problem"):
                    console.print(f"  Problem: {data['problem']}")
                if data.get("why_now"):
                    console.print(f"  Why now: {data['why_now']}")
                if data.get("founder_advice"):
                    console.print(f"  Advice: [yellow]{data['founder_advice']}[/yellow]")
            except (json.JSONDecodeError, KeyError):
                console.print(Markdown(result))


@app.command()
def plot():
    """Generate visualizations of YC company data."""
    from ycombigenerator.scraper import load
    from ycombigenerator.plot import (
        industry_timeline, batch_sizes, growing_tags, status_over_time,
        wordcloud_one_liners, geographic_distribution, industry_heatmap,
        founder_count_distribution, survival_rate_by_industry,
    )
    companies = load()

    with console.status("Generating plots..."):
        paths = {}
        paths["Industry share timeline"] = industry_timeline(companies)
        paths["Batch sizes"] = batch_sizes(companies)
        paths["Growing tags"] = growing_tags(companies)
        paths["Status over time"] = status_over_time(companies)
        paths["Word cloud"] = wordcloud_one_liners(companies)
        paths["Geographic distribution"] = geographic_distribution(companies)
        paths["Industry heatmap"] = industry_heatmap(companies)
        paths["Founder distribution"] = founder_count_distribution(companies)
        paths["Survival by industry"] = survival_rate_by_industry(companies)

    for name, path in paths.items():
        console.print(f"[green]{name}:[/green] {path}")


@app.command()
def info():
    """Show project info and configuration."""
    console.print("[bold]Y Combinator Generator[/bold]")
    key_status = "[green]set[/green]" if os.environ.get("OPENCODE_API_KEY") else "[red]not set[/red]"
    console.print(f"  OPENCODE_API_KEY: {key_status}")
    console.print(f"  OPENCODE_MODEL: {os.environ.get('OPENCODE_MODEL', 'deepseek-v4-flash (default)')}")
    from ycombigenerator.scraper import DATA_DIR
    console.print(f"  Data directory: {DATA_DIR}")


def main():
    app()
