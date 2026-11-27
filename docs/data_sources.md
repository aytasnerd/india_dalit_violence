# Data Sources

The live list is [`config/feeds.csv`](../config/feeds.csv). Summary:

| Source | Language | How | Notes |
|---|---|---|---|
| Google News search | English, Hindi | RSS search for "dalit", caste + violence terms, and "दलित" | Aggregates many outlets; the publisher is recorded in `section`. Replaced the old rss.app feeds in Nov 2026. |
| Dainik Bhaskar | Hindi | 16 state and section RSS feeds | Largest volume; strong coverage of the Hindi belt. |
| Times of India | English | 16 city and section RSS feeds | "Most Recent Stories" was dropped: it was the same URL as "India". |
| The Hindu | English | States, Cities, National RSS | |
| Indian Express Tamil / Malayalam / Bengali | Tamil, Malayalam, Bengali | Site-wide RSS | |
| Dalit Times | Hindi | Scrapes the crime category pages | Community outlet; every story kept without keyword filtering. |

Feed articles are kept only if they match a term in
[`config/keywords.txt`](../config/keywords.txt). In the October 2024 snapshot,
77 of 1,452 feed articles (about 5%) matched.

## Candidates to add

From the original source list (`data/legacy/2024-10-04/news_sources.csv`),
not yet set up: The Wire, Scroll.in, Newslaundry, The Print, Hindustan Times,
India Today, NDTV, Indian Express (English crime section), Deccan Herald,
LiveMint, The Statesman, Newsclick, Dalit Archive, Ambedkarite India.
