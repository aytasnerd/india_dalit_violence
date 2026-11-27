"""Fetch RSS feeds and turn their entries into Article records."""

from __future__ import annotations

import calendar
import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

from .models import Article, article_id, canonical_url, clean_text, now_utc, to_iso

log = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; india-dalit-violence-tracker/1.0; "
    "+https://github.com/aytasnerd/india_dalit_violence)"
)
TIMEOUT_SECONDS = 30
MAX_SUMMARY_CHARS = 1000


@dataclass
class Feed:
    source: str
    section: str
    language: str
    url: str


def load_feeds(path: Path) -> list[Feed]:
    with path.open(encoding="utf-8", newline="") as f:
        return [
            Feed(r["source"].strip(), r["section"].strip(), r["language"].strip(), r["url"].strip())
            for r in csv.DictReader(f)
            if r.get("url", "").strip()
        ]


def fetch(feed: Feed, session: requests.Session | None = None) -> bytes:
    http = session or requests
    resp = http.get(feed.url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.content


def _published(entry) -> str:
    for key in ("published_parsed", "updated_parsed"):
        parsed = entry.get(key)
        if parsed:
            return to_iso(datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc))
    return ""


def parse(feed: Feed, content: bytes, seen_at: str | None = None) -> list[Article]:
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"not a readable feed: {parsed.get('bozo_exception')}")

    seen_at = seen_at or now_utc()
    articles = []
    for entry in parsed.entries:
        url = entry.get("link", "").strip()
        title = clean_text(entry.get("title", ""))
        if not url or not title:
            continue
        section = feed.section
        # Google News results come from many outlets; keep the real publisher.
        publisher = entry.get("source", {}).get("title") if feed.source == "Google News" else None
        if publisher:
            section = f"{feed.section} ({publisher})"
        articles.append(
            Article(
                id=article_id(url),
                source=feed.source,
                section=section,
                language=feed.language,
                title=title,
                summary=clean_text(entry.get("summary", ""))[:MAX_SUMMARY_CHARS],
                url=canonical_url(url),
                published=_published(entry),
                first_seen=seen_at,
                matched_terms="",
            )
        )
    return articles
