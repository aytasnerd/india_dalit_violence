# India Dalit Violence Tracker

A volunteer effort to build a running, sourced record of news reports of
violence and discrimination against Dalit, Bahujan and Adivasi communities in
India, collected from outlets in English, Hindi, Tamil, Malayalam and Bengali.

Official figures (NCRB) arrive more than a year late, only as totals, and only
count cases where an FIR was registered. This project collects what the media
reports, every day, so it can be reviewed, organised and studied.

## What it does

Twice a day a GitHub Action:

1. reads about 40 news feeds listed in [`config/feeds.csv`](config/feeds.csv),
   plus the crime section of [Dalit Times](https://dalittimes.in/category/crime-2/);
2. keeps feed articles that mention any term in
   [`config/keywords.txt`](config/keywords.txt) (all Dalit Times crime stories
   are kept);
3. adds new ones to [`data/articles.csv`](data/articles.csv), skipping
   duplicates, and commits the result.

RSS feeds only hold the last day or two of stories, so the value of this
dataset comes from collecting **without gaps**. Each run is recorded in
[`data/collection_log.csv`](data/collection_log.csv), including any feeds that
failed.

**These are candidate articles, not verified incidents.** A keyword match means
an article *might* be relevant. Turning articles into incidents (what
happened, where, when) is the next stage of the project and needs human review.

## The data

`data/articles.csv` has one row per article:

| column | meaning |
|---|---|
| `id` | stable id derived from the article URL |
| `source`, `section` | outlet and feed section (for Google News, the real publisher is in brackets) |
| `language` | `en`, `hi`, `ta`, `ml` or `bn` |
| `title`, `summary` | as published in the feed, HTML removed |
| `url` | link to the article, tracking parameters removed |
| `published` | publication time in UTC (date only for Dalit Times), blank if unknown |
| `first_seen` | when this project first collected it |
| `matched_terms` | which keywords matched |

It starts with a one-off snapshot from 4 October 2024 (445 articles, imported
by `scripts/import_legacy.py`). The original raw files from that snapshot are
kept in `data/legacy/2024-10-04/`.

## Running it yourself

```bash
pip install -e ".[dev]"
python -m tracker collect          # fetch everything once
python -m tracker collect --dalit-times-pages 40   # backfill Dalit Times
pytest                             # run the tests
```

## Helping out

- **Add a feed:** add a row to `config/feeds.csv` (source, section, language
  code, RSS URL).
- **Improve keywords:** edit `config/keywords.txt`. Native speakers checking
  the Hindi, Tamil, Malayalam and Bengali terms would help a lot.
- **Review articles:** the next stage is tagging which articles describe a real
  incident.

Please be careful with what is shared from this data. Victims' names,
villages and photos can expose people to retaliation.

## Layout

```
config/       feeds and keywords (edit these)
src/tracker/  the collector
data/         collected articles and the run log
scripts/      one-off scripts
tests/        tests, with sample feed and page fixtures
notebooks/    exploratory notebooks
docs/         project notes
```
