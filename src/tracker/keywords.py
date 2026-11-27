"""Keyword matching used to decide whether an article is possibly relevant."""

from __future__ import annotations

import re
from pathlib import Path


def load_terms(path: Path) -> list[str]:
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


class KeywordMatcher:
    """Finds which configured terms appear in a piece of text.

    Latin-script terms must start at a word boundary (so "caste" does not
    match "broadcaster"); terms in Indian scripts match anywhere, because
    word boundaries are unreliable around combining vowel signs.
    """

    def __init__(self, terms: list[str]):
        self.patterns: list[tuple[str, re.Pattern]] = []
        for term in terms:
            escaped = re.escape(term)
            if term.isascii():
                pattern = re.compile(r"(?<![A-Za-z0-9])" + escaped, re.IGNORECASE)
            else:
                pattern = re.compile(escaped, re.IGNORECASE)
            self.patterns.append((term, pattern))

    @classmethod
    def from_file(cls, path: Path) -> "KeywordMatcher":
        return cls(load_terms(path))

    def find(self, *texts: str) -> list[str]:
        text = " ".join(t for t in texts if t)
        return [term for term, pattern in self.patterns if pattern.search(text)]
