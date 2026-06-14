# ycombigenerator

A Y Combinator company analyzer and hypothetical startup generator.

## Usage

```bash
# View dataset statistics
yc stats

# Analyze industry trends
yc analyze

# Predict next YC trends
yc trends

# Generate a hypothetical YC startup idea
export OPENCODE_API_KEY=sk-...
yc generate

# Generate a batch of ideas
yc generate --count 5

# Generate with a custom prompt direction
yc generate --prompt "focus on climate tech"
```

## Data

- **Primary:** 24msingh24/2024-YCombinator-All-Companies-Datasets (~4,800 companies, 2005-2024)
- **Supplement:** nikshepg/YC-Startup-Directory (~1,000 additional, up to Summer 2025)
- **Total:** 5,864 companies across 42 YC batches

Data is stored in `data/` directory as CSV files and is versioned in the repo.

## Setup

```bash
uv sync
yc refresh  # download latest dataset
```
