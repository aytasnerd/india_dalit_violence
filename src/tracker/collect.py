"""One collection run: fetch every source, keep relevant articles, save."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import requests

from . import dalittimes, feeds, store
from .keywords import KeywordMatcher
from .models import Article, now_utc

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
FEEDS_FILE = ROOT / "config" / "feeds.csv"
KEYWORDS_FILE = ROOT / "config" / "keywords.txt"
ARTICLES_FILE = ROOT / "data" / "articles.csv"
LOG_FILE = ROOT / "data" / "collection_log.csv"


@dataclass
class RunResult:
    fetched: int = 0
    new: list[Article] = field(default_factory=list)
    ok: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def filter_relevant(articles: list[Article], matcher: KeywordMatcher) -> list[Article]:
    relevant = []
    for a in articles:
        terms = matcher.find(a.title, a.summary)
        if terms:
            a.matched_terms = "; ".join(terms)
            relevant.append(a)
    return relevant


def run(
    feeds_file: Path = FEEDS_FILE,
    keywords_file: Path = KEYWORDS_FILE,
    articles_file: Path = ARTICLES_FILE,
    log_file: Path | None = LOG_FILE,
    dalit_times_pages: int = 3,
) -> RunResult:
    result = RunResult()
    matcher = KeywordMatcher.from_file(keywords_file)
    session = requests.Session()
    seen_at = now_utc()
    collected: list[Article] = []

    for feed in feeds.load_feeds(feeds_file):
        label = f"{feed.source} / {feed.section}"
        try:
            items = feeds.parse(feed, feeds.fetch(feed, session), seen_at=seen_at)
        except Exception as exc:  # one broken feed must not stop the run
            log.warning("FAILED %s: %s", label, exc)
            result.failed.append(label)
            continue
        result.ok.append(label)
        result.fetched += len(items)
        relevant = filter_relevant(items, matcher)
        log.info("%s: %d items, %d relevant", label, len(items), len(relevant))
        collected.extend(relevant)

    try:
        stories = dalittimes.scrape(store.known_ids(articles_file), dalit_times_pages, session)
        result.ok.append("Dalit Times / Crime")
        result.fetched += len(stories)
        collected.extend(stories)
    except Exception as exc:
        log.warning("FAILED Dalit Times: %s", exc)
        result.failed.append("Dalit Times / Crime")

    result.new = store.append_new(articles_file, collected)
    log.info(
        "Done: %d sources ok, %d failed, %d items fetched, %d new relevant articles saved",
        len(result.ok), len(result.failed), result.fetched, len(result.new),
    )
    if log_file:
        store.append_log(
            log_file,
            {
                "run_at": seen_at,
                "feeds_ok": len(result.ok),
                "feeds_failed": len(result.failed),
                "failed_feeds": "; ".join(result.failed),
                "fetched": result.fetched,
                "new_articles": len(result.new),
            },
        )
    return result
