from pathlib import Path

import pytest

from tracker import collect, dalittimes, feeds, store
from tracker.keywords import KeywordMatcher
from tracker.models import article_id, canonical_url, clean_text

FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]
FEED = feeds.Feed("Sample News", "National", "en", "https://news.example.com/rss")


# --- keywords ---------------------------------------------------------------

@pytest.fixture
def matcher():
    return KeywordMatcher.from_file(ROOT / "config" / "keywords.txt")


def test_matches_english_word_starts(matcher):
    assert matcher.find("Upper-caste men attack Dalits") == ["dalit", "caste"]
    assert matcher.find("Casteist slurs reported") == ["caste"]


def test_does_not_match_inside_other_words(matcher):
    assert matcher.find("Broadcaster's forecaster says rain") == []


def test_matches_indian_scripts(matcher):
    assert "दलित" in matcher.find("दलित युवक को पीटा")
    assert "தலித்" in matcher.find("தலித் இளைஞர் மீது தாக்குதல்")
    assert "ദളിത്" in matcher.find("ദളിത് യുവാവിന് മർദനം")
    assert "দলিত" in matcher.find("দলিত যুবককে মারধর")


def test_tamil_achieved_is_not_caste(matcher):
    # "சாதித்தார்" (achieved) contains the root "சாதி" (caste).
    assert matcher.find("இந்திய அணி சாதித்தார்") == []


def test_every_configured_term_matches_itself(matcher):
    for term, _ in matcher.patterns:
        assert term in matcher.find(term), term


# --- models -----------------------------------------------------------------

def test_canonical_url_strips_tracking():
    assert (
        canonical_url("HTTPS://News.Example.com/a?id=5&utm_source=x&fbclid=y#top")
        == "https://news.example.com/a?id=5"
    )


def test_article_id_ignores_tracking_params():
    assert article_id("https://x.com/a?utm_medium=rss") == article_id("https://x.com/a")


def test_clean_text_strips_html():
    assert clean_text("<p>Hello <b>world</b></p>\n  ok") == "Hello world ok"


# --- feeds ------------------------------------------------------------------

def test_parse_feed():
    articles = feeds.parse(FEED, (FIXTURES / "sample_feed.xml").read_bytes(), seen_at="T")
    assert len(articles) == 3  # the untitled entry is skipped
    first = articles[0]
    assert first.url == "https://news.example.com/story-1"
    assert first.published == "2024-10-04T12:17:27+00:00"
    assert first.summary.startswith("Police registered a case under the SC/ST")
    assert first.first_seen == "T"
    assert articles[2].published == ""


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        feeds.parse(FEED, b"<html>not a feed")


def test_filter_relevant(matcher):
    articles = feeds.parse(FEED, (FIXTURES / "sample_feed.xml").read_bytes())
    relevant = collect.filter_relevant(articles, matcher)
    assert [a.url.rsplit("/", 1)[1] for a in relevant] == ["story-1", "story-3"]
    assert relevant[0].matched_terms == "dalit; SC/ST; prevention of atrocities"


def test_load_feeds_config():
    loaded = feeds.load_feeds(ROOT / "config" / "feeds.csv")
    assert len(loaded) > 30
    assert all(f.url.startswith("https://") and f.language for f in loaded)
    assert len({f.url for f in loaded}) == len(loaded), "duplicate feed URLs"


# --- Dalit Times ------------------------------------------------------------

def test_parse_dalittimes_page():
    articles = dalittimes.parse_page((FIXTURES / "dalittimes_page.html").read_bytes())
    assert len(articles) == 2
    assert articles[0].title == "दलित युवक को लात-घूंसों से पीटा"
    assert articles[0].published == "2024-10-03"
    assert articles[1].published == "2024-09-19"
    assert articles[0].matched_terms == dalittimes.MATCH_NOTE


@pytest.mark.parametrize(
    "text,expected",
    [
        ("अक्टूबर 3, 2024", "2024-10-03"),
        ("फ़रवरी 29, 2024", "2024-02-29"),
        ("दिसंबर 1, 2023", "2023-12-01"),
        ("October 3, 2024", "2024-10-03"),
        ("", ""),
        ("कल", ""),
    ],
)
def test_parse_hindi_date(text, expected):
    assert dalittimes.parse_hindi_date(text) == expected


class FakeResponse:
    def __init__(self, status, content=b""):
        self.status_code, self.content = status, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self, pages):
        self.pages, self.requested = pages, []

    def get(self, url, **_):
        self.requested.append(url)
        return self.pages.get(url, FakeResponse(404))


def test_dalittimes_stops_when_nothing_new():
    html = (FIXTURES / "dalittimes_page.html").read_bytes()
    session = FakeSession({dalittimes.page_url(p): FakeResponse(200, html) for p in (1, 2, 3)})
    found = dalittimes.scrape(set(), max_pages=3, session=session)
    # Page 2 repeats page 1's stories, so the run stops there.
    assert len(found) == 2
    assert len(session.requested) == 2


# --- store and full run -----------------------------------------------------

def test_append_new_dedupes(tmp_path):
    path = tmp_path / "articles.csv"
    articles = feeds.parse(FEED, (FIXTURES / "sample_feed.xml").read_bytes())
    assert len(store.append_new(path, articles)) == 3
    assert len(store.append_new(path, articles + articles)) == 0
    assert len(path.read_text(encoding="utf-8").splitlines()) == 4  # header + 3


def test_run_survives_failing_sources(tmp_path, monkeypatch):
    feeds_file = tmp_path / "feeds.csv"
    feeds_file.write_text(
        "source,section,language,url\n"
        "Good,All,en,https://good.example/rss\n"
        "Bad,All,en,https://bad.example/rss\n",
        encoding="utf-8",
    )
    sample = (FIXTURES / "sample_feed.xml").read_bytes()

    def fake_fetch(feed, session=None):
        if "bad" in feed.url:
            raise ConnectionError("down")
        return sample

    monkeypatch.setattr(feeds, "fetch", fake_fetch)
    monkeypatch.setattr(dalittimes, "scrape", lambda *a, **k: [])

    out, log = tmp_path / "articles.csv", tmp_path / "log.csv"
    result = collect.run(feeds_file, ROOT / "config" / "keywords.txt", out, log)
    assert result.failed == ["Bad / All"]
    assert len(result.new) == 2
    assert "Bad / All" in log.read_text(encoding="utf-8")

    again = collect.run(feeds_file, ROOT / "config" / "keywords.txt", out, log)
    assert again.new == []
