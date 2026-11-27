# Daily collector — design (short)

**Why:** the October 2024 snapshot was a one-off, and RSS feeds only keep a day
or two of stories, so every day without collection is permanently lost. The
first step of the revamp is a reliable, unattended collector that builds a
continuous dataset. Agreed with the project owner on 2026-11-27.

**Goals:** one runnable Python collector for all RSS feeds plus Dalit Times;
multilingual keyword filter; deduplicated single CSV; runs twice daily on
GitHub Actions and commits new data; secrets and clutter removed from the repo.

**Non-goals (later stages):** incident extraction, cross-outlet event merging,
human review tooling, a public website, Twitter collection.

**Approaches considered:**
- *Store every fetched article* (~1,500/day): allows re-filtering later, but
  grows by roughly 500 MB/year in git. Rejected.
- *Store only keyword matches* (~50–100/day) — **chosen.** Small and
  reviewable. Trade-off: terms added later can't be applied to past days, so
  the keyword list is deliberately broad.
- *Run on a server / cron on a laptop:* needs upkeep and stops when the laptop
  is off. GitHub Actions is free and needs no maintenance.

**Calls made by Claude** (owner can change): twice-daily schedule; Google
News search feeds replace the expiring rss.app feeds; Latin-script terms match
at word starts and Indian-script terms anywhere; Dalit Times reads up to 3
pages per run and stops at the first page with nothing new; old raw files kept
under `data/legacy/2024-10-04/`; pandas and tweepy dropped from dependencies.
