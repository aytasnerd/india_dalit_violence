"""One-time import of the October 2024 snapshot into data/articles.csv.

Reads the old raw files in data/legacy/2024-10-04/, applies the same keyword
filter as the daily collector, and appends anything relevant. Safe to re-run:
articles already stored are skipped.

    python scripts/import_legacy.py
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tracker import collect, dalittimes, store  # noqa: E402
from tracker.keywords import KeywordMatcher  # noqa: E402
from tracker.models import Article, article_id, canonical_url, clean_text, to_iso  # noqa: E402

LEGACY = ROOT / "data" / "legacy" / "2024-10-04"
LANGUAGES = {
    "Indian Express Bengali": "bn",
    "Indian Express Malayalam": "ml",
    "Indian Express Tamil": "ta",
    "Dainik Bhaskar": "hi",
}

csv.field_size_limit(sys.maxsize)


def _iso(text: str) -> str:
    if not text:
        return ""
    try:
        return to_iso(parsedate_to_datetime(text))
    except (TypeError, ValueError):
        pass
    try:
        return to_iso(datetime.fromisoformat(text))
    except ValueError:
        return ""


def feed_articles() -> list[Article]:
    out = []
    with (LEGACY / "feeds" / "master_feed.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            url, title = (r.get("link") or "").strip(), clean_text(r.get("title") or "")
            if not url or not title:
                continue
            source = r["FeedName"]
            section = (r.get("Section") or "").strip()
            if source == "Google News":
                section = f"Search: {section}"
            out.append(
                Article(
                    id=article_id(url),
                    source=source,
                    section=section or "All",
                    language=LANGUAGES.get(source, "en"),
                    title=title,
                    summary=clean_text(r.get("summary") or "")[:1000],
                    url=canonical_url(url),
                    published=_iso(r.get("published") or ""),
                    first_seen=_iso(r.get("FetchTime") or ""),
                    matched_terms="",
                )
            )
    return out


def dalit_times_articles() -> list[Article]:
    out = []
    with (LEGACY / "dalittimes" / "stories.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if not r.get("link"):
                continue
            out.append(
                Article(
                    id=article_id(r["link"]),
                    source=dalittimes.SOURCE,
                    section=dalittimes.SECTION,
                    language="hi",
                    title=clean_text(r["title"]),
                    summary=clean_text(r.get("summary") or ""),
                    url=canonical_url(r["link"]),
                    published=dalittimes.parse_hindi_date(r.get("date") or ""),
                    first_seen="2024-10-04T00:00:00+00:00",
                    matched_terms=dalittimes.MATCH_NOTE,
                )
            )
    return out


def main() -> None:
    matcher = KeywordMatcher.from_file(collect.KEYWORDS_FILE)
    feed_items = feed_articles()
    relevant = collect.filter_relevant(feed_items, matcher)
    stories = dalit_times_articles()
    added = store.append_new(collect.ARTICLES_FILE, relevant + stories)
    print(
        f"Feed items: {len(feed_items)}, keyword matches: {len(relevant)}, "
        f"Dalit Times stories: {len(stories)}, newly added: {len(added)}"
    )


if __name__ == "__main__":
    main()
