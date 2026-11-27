"""Scrape the crime section of Dalit Times (dalittimes.in).

Every story in this section is relevant, so these are kept without keyword
filtering.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .feeds import TIMEOUT_SECONDS, USER_AGENT
from .models import Article, article_id, canonical_url, clean_text, now_utc

log = logging.getLogger(__name__)

BASE_URL = "https://dalittimes.in/category/crime-2/"
SOURCE = "Dalit Times"
SECTION = "Crime"
MATCH_NOTE = "source: Dalit Times crime section"

HINDI_MONTHS = {
    "जनवरी": 1, "फ़रवरी": 2, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4, "मई": 5,
    "जून": 6, "जुलाई": 7, "अगस्त": 8, "सितम्बर": 9, "सितंबर": 9,
    "अक्टूबर": 10, "अक्तूबर": 10, "नवम्बर": 11, "नवंबर": 11,
    "दिसम्बर": 12, "दिसंबर": 12,
}
_DATE_RE = re.compile(r"(\S+)\s+(\d{1,2}),\s*(\d{4})")


def page_url(page: int) -> str:
    return BASE_URL if page <= 1 else f"{BASE_URL}page/{page}/"


def parse_hindi_date(text: str) -> str:
    """'अक्टूबर 3, 2024' -> '2024-10-03'. Returns '' if not recognised."""
    m = _DATE_RE.search(text or "")
    if not m:
        return ""
    month = HINDI_MONTHS.get(m.group(1))
    if not month:
        try:
            month = datetime.strptime(m.group(1)[:3], "%b").month
        except ValueError:
            return ""
    return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(2)):02d}"


def parse_page(html: str | bytes, seen_at: str | None = None) -> list[Article]:
    seen_at = seen_at or now_utc()
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    for item in soup.select("div.post-item"):
        link = item.select_one("a.post-thumbnail") or item.select_one(".entry-title a")
        title = item.select_one(".entry-title")
        if not link or not link.get("href") or not title:
            continue
        date = item.select_one(".post-date")
        summary = item.select_one(".post-content p")
        url = link["href"]
        articles.append(
            Article(
                id=article_id(url),
                source=SOURCE,
                section=SECTION,
                language="hi",
                title=clean_text(title.get_text(" ")),
                summary=clean_text(summary.get_text(" ")) if summary else "",
                url=canonical_url(url),
                published=parse_hindi_date(date.get_text(" ") if date else ""),
                first_seen=seen_at,
                matched_terms=MATCH_NOTE,
            )
        )
    return articles


def scrape(known_ids: set[str], max_pages: int = 3, session=None) -> list[Article]:
    """Read pages newest-first, stopping at the first page with nothing new.

    Daily runs only need a page or two; pass a larger max_pages to backfill.
    """
    http = session or requests
    seen = set(known_ids)
    found: list[Article] = []
    for page in range(1, max_pages + 1):
        resp = http.get(page_url(page), headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
        if resp.status_code == 404:
            break
        resp.raise_for_status()
        page_articles = parse_page(resp.content)
        new = [a for a in page_articles if a.id not in seen]
        seen.update(a.id for a in new)
        found.extend(new)
        log.info("Dalit Times page %d: %d stories, %d new", page, len(page_articles), len(new))
        if not page_articles or not new:
            break
    return found
