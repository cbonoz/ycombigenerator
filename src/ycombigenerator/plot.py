from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from ycombigenerator.scraper import Company, batch_year

FIGS_DIR = Path(__file__).resolve().parent.parent.parent / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)


def industry_timeline(companies: dict[str, Company], top_n: int = 8) -> str:
    years_data: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    years_total: dict[int, int] = defaultdict(int)
    for c in companies.values():
        yr = batch_year(c.batch)
        if yr is None or yr < 2010:
            continue
        years_total[yr] += 1
        for ind in c.industries:
            if ind:
                years_data[yr][ind] += 1

    all_inds: Counter = Counter()
    for yr_data in years_data.values():
        all_inds.update(yr_data)
    top_inds = [ind for ind, _ in all_inds.most_common(top_n)]

    years = sorted(years_data)
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Set2(range(len(top_inds)))

    for ind, color in zip(top_inds, colors):
        pcts = [
            (years_data[yr].get(ind, 0) / years_total[yr]) * 100 if years_total[yr] > 0 else 0
            for yr in years
        ]
        ax.plot(years, pcts, label=ind, color=color, linewidth=2, marker="o", markersize=3)

    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Share of Companies (%)", fontsize=12)
    ax.set_title("YC Industry Share Over Time", fontsize=14, fontweight="bold")
    ax.legend(frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    path = FIGS_DIR / "industry_timeline.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def batch_sizes(companies: dict[str, Company]) -> str:
    batches: Counter = Counter()
    for c in companies.values():
        if c.batch:
            batches[c.batch] += 1

    sorted_batches = sorted(batches, key=lambda b: (batch_year(b) or 0, b))
    batch_labels = sorted_batches
    counts = [batches[b] for b in sorted_batches]

    fig, ax = plt.subplots(figsize=(14, 5))
    bars = ax.bar(range(len(batch_labels)), counts, color=plt.cm.Blues(0.6))
    ax.set_xticks(range(len(batch_labels)))
    ax.set_xticklabels(batch_labels, rotation=90, fontsize=8)
    ax.set_xlabel("Batch", fontsize=12)
    ax.set_ylabel("Companies", fontsize=12)
    ax.set_title("YC Batch Sizes", fontsize=14, fontweight="bold")
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    path = FIGS_DIR / "batch_sizes.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def growing_tags(companies: dict[str, Company], top_n: int = 10) -> str:
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

    growth = []
    all_tags = set(tags_past) | set(tags_recent)
    for tag in all_tags:
        past = tags_past.get(tag, 0)
        recent = tags_recent.get(tag, 0)
        if past == 0 and recent == 0:
            continue
        pct = ((recent - past) / max(past, 1)) * 100
        growth.append((tag, past, recent, pct))

    growth.sort(key=lambda x: -x[3])
    top = growth[:top_n]

    fig, ax = plt.subplots(figsize=(10, 6))
    tags = [t[0] for t in top]
    pcts = [t[3] for t in top]
    colors = ["#2ecc71" if p > 0 else "#e74c3c" for p in pcts]
    bars = ax.barh(range(len(tags)), pcts, color=colors)
    ax.set_yticks(range(len(tags)))
    ax.set_yticklabels(tags, fontsize=10)
    ax.set_xlabel("Growth %", fontsize=12)
    ax.set_title("Fastest Growing YC Tags (2023+ vs before)", fontsize=14, fontweight="bold")
    ax.axvline(x=0, color="black", linewidth=0.5)
    for i, (_, past, recent, pct) in enumerate(top):
        label = f"  {past}→{recent}"
        ax.text(pct + 5 if pct >= 0 else pct - 5, i, label, va="center", fontsize=9)
    fig.tight_layout()

    path = FIGS_DIR / "growing_tags.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def status_over_time(companies: dict[str, Company]) -> str:
    years_status: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    years_set: set[int] = set()
    for c in companies.values():
        yr = batch_year(c.batch)
        if yr is None or yr < 2010:
            continue
        years_set.add(yr)
        status = c.status if c.status else "Unknown"
        years_status[yr][status] += 1

    years = sorted(years_set)
    statuses = ["Active", "Acquired", "Inactive", "Public"]
    data = {s: [years_status[yr].get(s, 0) for yr in years] for s in statuses}

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = {"Active": "#2ecc71", "Acquired": "#3498db", "Inactive": "#e74c3c", "Public": "#f39c12"}
    ax.stackplot(years, [data[s] for s in statuses], labels=statuses,
                 colors=[colors[s] for s in statuses], alpha=0.85)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_ylabel("Number of Companies", fontsize=12)
    ax.set_title("YC Company Status Over Time", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", frameon=True, fancybox=True)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    path = FIGS_DIR / "status_over_time.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def wordcloud_one_liners(companies: dict[str, Company]) -> str:
    text = " ".join(c.one_liner for c in companies.values() if c.one_liner)

    stop_words = {
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
    words = [w.strip(".,!?;:()[]{}'\"-").lower() for w in text.split()
             if w.strip(".,!?;:()[]{}'\"-").lower() not in stop_words and len(w) > 2]
    word_counts = Counter(words)
    top = word_counts.most_common(60)

    if not top:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Not enough data", ha="center", va="center", fontsize=20)
        path = FIGS_DIR / "wordcloud.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return str(path)

    words, counts = zip(*top)
    font_sizes = [max(10, (c / max(counts)) * 60 + 10) for c in counts]
    fig, ax = plt.subplots(figsize=(14, 10))
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(words)))
    np.random.shuffle(colors)
    for word, size, color in zip(words, font_sizes, colors):
        x = np.random.uniform(0, 1)
        y = np.random.uniform(0, 1)
        ax.text(x, y, word, fontsize=size, color=color, ha="center", va="center", alpha=0.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Most Common Words in YC One-Liners", fontsize=16, fontweight="bold", pad=20)
    fig.tight_layout()

    path = FIGS_DIR / "wordcloud.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def geographic_distribution(companies: dict[str, Company], top_n: int = 12) -> str:
    regions: Counter = Counter()
    for c in companies.values():
        if c.region:
            region = c.region.split("/")[0].strip()
            regions[region] += 1

    top = regions.most_common(top_n)
    labels = [t[0] for t in top]
    counts = [t[1] for t in top]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(labels)), counts, color=plt.cm.Set2(np.linspace(0, 1, len(labels))))
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Number of Companies", fontsize=12)
    ax.set_title("Top YC Company Regions", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    for i, (_, v) in enumerate(top):
        ax.text(v + 5, i, str(v), va="center", fontsize=9)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()

    path = FIGS_DIR / "geographic_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def industry_heatmap(companies: dict[str, Company]) -> str:
    years_data: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    years_set: set[int] = set()
    for c in companies.values():
        yr = batch_year(c.batch)
        if yr is None or yr < 2015 or yr > 2025:
            continue
        years_set.add(yr)
        for ind in c.industries:
            if ind:
                years_data[yr][ind] += 1

    years = sorted(years_set)
    all_inds: Counter = Counter()
    for yr_data in years_data.values():
        all_inds.update(yr_data)
    top_inds = [ind for ind, _ in all_inds.most_common(10)]

    matrix = np.zeros((len(top_inds), len(years)))
    for j, yr in enumerate(years):
        total = sum(years_data[yr].values())
        for i, ind in enumerate(top_inds):
            matrix[i, j] = (years_data[yr].get(ind, 0) / max(total, 1)) * 100

    fig, ax = plt.subplots(figsize=(12, 7))
    im = ax.imshow(matrix, aspect="auto", cmap="YlOrRd", vmin=0, vmax=40)
    ax.set_xticks(range(len(years)))
    ax.set_xticklabels(years, fontsize=9)
    ax.set_yticks(range(len(top_inds)))
    ax.set_yticklabels(top_inds, fontsize=9)
    ax.set_title("Industry Share by Year (%)", fontsize=14, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("% of Batch", fontsize=10)

    for i in range(len(top_inds)):
        for j in range(len(years)):
            val = matrix[i, j]
            if val > 0:
                color = "white" if val > 20 else "black"
                ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=7, color=color)
    fig.tight_layout()

    path = FIGS_DIR / "industry_heatmap.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def founder_count_distribution(companies: dict[str, Company]) -> str:
    counts: Counter = Counter()
    for c in companies.values():
        n = len(c.founders)
        if n > 0:
            counts[n] += 1

    if not counts:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, "No founder data available", ha="center", va="center", fontsize=14)
        path = FIGS_DIR / "founder_distribution.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return str(path)

    max_n = max(counts.keys())
    xs = list(range(1, max_n + 1))
    ys = [counts.get(x, 0) for x in xs]
    total = sum(ys)
    pcts = [y / total * 100 for y in ys]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(xs, ys, color=plt.cm.Blues(np.linspace(0.4, 0.8, len(xs))))
    ax.set_xlabel("Number of Founders", fontsize=12)
    ax.set_ylabel("Companies", fontsize=12)
    ax.set_title("Founder Count Distribution", fontsize=14, fontweight="bold")
    ax.set_xticks(xs)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    for i, (x, y, p) in enumerate(zip(xs, ys, pcts)):
        ax.text(x, y + max(ys) * 0.02, f"{y} ({p:.0f}%)", ha="center", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    path = FIGS_DIR / "founder_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def survival_rate_by_industry(companies: dict[str, Company], top_n: int = 10) -> str:
    ind_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in companies.values():
        for ind in c.industries:
            if ind:
                ind_stats[ind][c.status] += 1

    data = []
    for ind, stats in ind_stats.items():
        total = sum(stats.values())
        if total < 10:
            continue
        active = stats.get("Active", 0)
        acquired = stats.get("Acquired", 0)
        survival = (active + acquired) / total * 100
        data.append((ind, total, active, acquired, survival))

    data.sort(key=lambda x: -x[4])
    top = data[:top_n]

    fig, ax = plt.subplots(figsize=(10, 6))
    labels = [t[0] for t in top]
    survival_rates = [t[4] for t in top]
    colors = ["#2ecc71" if s > 60 else "#f39c12" if s > 40 else "#e74c3c" for s in survival_rates]
    bars = ax.barh(range(len(labels)), survival_rates, color=colors)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Survival Rate (%)", fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_title("Company Survival Rate by Industry (Active + Acquired)", fontsize=12, fontweight="bold")
    for i, (_, total, active, acquired, rate) in enumerate(top):
        ax.text(rate + 1, i, f"{rate:.0f}% ({active}+{acquired}/{total})", va="center", fontsize=8)
    ax.axvline(x=50, color="gray", linestyle="--", alpha=0.5)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()

    path = FIGS_DIR / "survival_by_industry.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)
