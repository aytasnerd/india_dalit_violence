"""The article record shared by every source, and helpers to build it."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup


@dataclass
class Article:
    id: str
    source: str
    section: str
    language: str
    title: str
    summary: str
    url: str
    published: str  # ISO 8601 UTC, or "" when the source gives no usable date
    first_seen: str  # ISO 8601 UTC, when this project first collected it
    matched_terms: str  # "; "-joined keywords, or a note for sources kept whole

    def to_row(self) -> dict:
        return asdict(self)


FIELDNAMES = [f.name for f in fields(Article)]

_TRACKING_PREFIXES = ("utm_", "fbclid", "gclid")


def canonical_url(url: str) -> str:
    """Strip tracking parameters and fragments so the same story dedupes."""
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith(_TRACKING_PREFIXES)
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), "")
    )


def article_id(url: str) -> str:
    return hashlib.sha1(canonical_url(url).encode("utf-8")).hexdigest()[:16]


def clean_text(html_or_text: str) -> str:
    """Turn an HTML snippet into plain single-spaced text."""
    if not html_or_text:
        return ""
    text = BeautifulSoup(html_or_text, "html.parser").get_text(" ")
    return " ".join(text.split())


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
