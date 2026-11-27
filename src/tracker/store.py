"""Read and append to the CSV files under data/."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import FIELDNAMES, Article

LOG_FIELDS = ["run_at", "feeds_ok", "feeds_failed", "failed_feeds", "fetched", "new_articles"]


def known_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as f:
        return {row["id"] for row in csv.DictReader(f)}


def append_new(path: Path, articles: list[Article]) -> list[Article]:
    """Append articles whose id is not already stored; returns those added."""
    existing = known_ids(path)
    new: list[Article] = []
    for a in articles:
        if a.id not in existing:
            existing.add(a.id)
            new.append(a)
    if not new:
        return new

    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerows(a.to_row() for a in new)
    return new


def append_log(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
