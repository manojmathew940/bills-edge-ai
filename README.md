# Bills AI Analyst

This project is a Buffalo Bills-focused AI backend that is intended to combine:

- structured game analytics
- optional retrieval from Bills-related sources
- LLM-powered explanation generation

The goal is to answer questions such as:

- Why did the Bills lose game X?
- Why did they take 8 sacks?
- Would more blitzing have helped?
- What would have helped them win?

The long-term direction is to support a hybrid architecture where:

1. Bills game data is ingested and cleaned into an analysis-ready dataset.
2. An analytics layer computes relevant football metrics and evidence.
3. Retrieval or web search can add supporting context from articles and reports.
4. An LLM synthesizes the evidence into a grounded explanation.

Future extensions may include:

- comparing web search vs. RAG for Bills-specific questions
- adding a Bills draft assistant
- exposing the system through a website and API

## Current Status

The repo is currently an early FastAPI scaffold with a basic application entry point in `app/main.py`.

## Raw Data Ingestion

Download raw Bills play-by-play rows for one season:

```bash
python3 app/data_ingestion.py 2024
```

This saves the filtered raw source columns to:

```text
data/raw/bills_play_by_play_2024_raw.csv.gz
```

The script also writes a metadata file next to the raw data:

```text
data/raw/bills_play_by_play_2024_raw.metadata.json
```

The raw data is intentionally saved before normalization so the source columns can be inspected before deciding the analysis-ready schema mapping. The ingestion script validates the season range, checks required nflverse columns, limits the compressed source size, and only writes into `data/raw/`.

## Processed Play Data

Create the first curated play-level dataset for a season:

```bash
python3 app/data_cleaning.py 2024
```

This reads the raw Bills play-by-play file and writes:

```text
data/processed/bills_plays_2024.parquet
```
