# Podcast Duration: Implementation Plan

**Status: Implemented**

## Goal

Add episode duration (in minutes) to the Overcast podcast data pipeline so the monthly summary can report **total minutes listened** and show per-episode duration.

## Background

The Overcast OPML export has no duration field. The `progress` attribute exists but is cleared to `null` for `played="1"` episodes, making it useless for finished episodes. However, each feed's RSS XML (`xmlUrl` in the OPML) reliably contains `<itunes:duration>` per episode.

### Experiment Results: RSS Duration Availability

| Feed | Platform | `<itunes:duration>` format | Works? |
| --- | --- | --- | --- |
| Planet Money | NPR / Megaphone | Seconds (`1541`) | ✅ |
| Decoder | Megaphone | Seconds (`3726`) | ✅ |
| Mobile Dev Memo | Anchor / Spotify | `HH:MM:SS` (`00:46:06`) | ✅ |
| The Talk Show | Libsyn | `HH:MM:SS` (`02:31:53`) | ✅ |
| 一席 | XiaoYuZhou | `MM:SS` (`24:09`) | ✅ |
| Stratechery | Passport (paywalled) | `HH:MM:SS` (`00:54:14`) | ✅ (auth token baked into URL) |
| Acquired | Transistor | Seconds (`14360`) | ✅ |

**3 duration formats** to handle: raw seconds, `MM:SS`, and `HH:MM:SS` — all trivially parseable.

**Overcast URL (`overcastUrl`) was also tested** — duration is NOT in the static HTML. It's computed client-side via JavaScript `player.duration` after audio loads. Not usable without a headless browser.

## Decisions

1. **Fetch cadence**: Only fetch durations for episodes where `duration_seconds IS NULL`. This makes subsequent syncs fast (skip episodes already enriched).

2. **No standalone command**: Duration fetching is part of the `overcast-sync` command. After `overcast-to-sqlite` imports the OPML, we enrich episodes with duration from RSS. A one-time backfill can be done by running `overcast-sync` once after the feature is built.

---

## Approach: Fetch Duration from RSS Feeds

1. For each feed in the DB with episodes missing duration, fetch its `xmlUrl` RSS XML
2. Parse `<itunes:duration>` from each RSS `<item>`
3. Match RSS items to DB episodes by **title** (scoped to feed)
4. Store duration in a new `duration_seconds` column on the `episodes` table
5. Aggregate in analytics and surface in the markdown report

### Known Limitations

- **Old episodes**: Most RSS feeds only keep 50-300 recent episodes. Episodes that fell off the feed will have `duration_seconds = NULL`.
- **Feed availability**: Some feeds may be temporarily down or return errors. These should be skipped gracefully.
- **Title collisions**: Within a single feed, duplicate episode titles are theoretically possible but extremely rare. If it happens, both episodes get the same duration (acceptable).

---

## Proposed Changes

### 1. Duration Parser Utility

#### [NEW] `src/overcast/duration.py`

A pure utility module for parsing `<itunes:duration>` values:

```python
def parse_duration(value: str) -> int | None:
    """Parse itunes:duration to seconds.

    Handles: raw seconds ("1541"), MM:SS ("24:09"), HH:MM:SS ("02:31:53").
    Returns None on failure.
    """
```

### 2. RSS Feed Fetcher

#### [NEW] `src/overcast/rss_fetcher.py`

Fetches RSS feeds and extracts per-episode duration:

```python
class RSSFetcher:
    def fetch_durations(self, feeds: list[dict]) -> dict[tuple[int, str], int]:
        """Fetch durations for all feeds.

        Args:
            feeds: List of dicts with 'xmlUrl' and 'overcastId'.

        Returns:
            Mapping of (feedId, episode_title) -> duration_seconds.
        """
```

Key design decisions:
- Use `urllib.request` (stdlib, no extra dependency) with a 10s timeout per feed
- Parse RSS XML with `xml.etree.ElementTree` (stdlib)
- Handle the `itunes:duration` namespace (`http://www.itunes.com/dtds/podcast-1.0.dtd`)
- HTML-unescape titles for matching (OPML uses XML entities like `&#x2019;`)
- Log warnings for feeds that fail, but continue with others
- ~35 HTTP requests total (one per feed, not per episode)

### 3. Database Schema Change

#### [MODIFY] `src/overcast/models.py`

Add migration to add `duration_seconds` column to the `episodes` table:

```sql
ALTER TABLE episodes ADD COLUMN duration_seconds INTEGER;
```

Since `episodes` is created by `overcast-to-sqlite`, we add the column via `ALTER TABLE` after import (idempotent — check if column exists first).

### 4. Importer Integration

#### [MODIFY] `src/overcast/importer.py`

After `overcast-to-sqlite` runs, call the RSS fetcher:

1. Ensure `duration_seconds` column exists on `episodes`
2. Query feeds needing enrichment: `SELECT DISTINCT f.overcastId, f.xmlUrl FROM feeds f JOIN episodes e ON f.overcastId = e.feedId WHERE e.duration_seconds IS NULL AND f.xmlUrl IS NOT NULL`
3. Call `RSSFetcher.fetch_durations(feeds)` — returns `(feedId, title) → seconds`
4. Update: `UPDATE episodes SET duration_seconds = ? WHERE feedId = ? AND title = ? AND duration_seconds IS NULL`
5. Report stats: `"Durations enriched: 450/520 episodes"`

### 5. Analytics Update

#### [MODIFY] `src/overcast/analytics.py`

Add `minutes_listened` to the monthly analysis:

```sql
SELECT
    strftime('%Y', e.userUpdatedDate) as year,
    strftime('%m', e.userUpdatedDate) as month,
    SUM(e.duration_seconds) as total_seconds
FROM episodes e
WHERE e.played = 1
  AND e.userUpdatedDate IS NOT NULL
  AND e.duration_seconds IS NOT NULL
```

#### [MODIFY] `src/overcast/models.py`

Add `minutes_listened INTEGER DEFAULT 0` to the `analysis` table schema.

### 6. Publisher & Markdown Generator

#### [MODIFY] `src/publish/publisher.py`

- Update `_get_overcast_analysis()` query to include `minutes_listened`
- Pass `minutes_listened` into the `data['overcast']` dict
- Add `minutes_listened` to `compute_comparisons()` metrics

#### [MODIFY] `src/publish/markdown_generator.py`

- Update `_generate_overcast_section()` to display listening time:
  ```
  - **Time Listened**: 12h 34m (MoM: +15.2%, YoY: +8.1%)
  ```
- Optionally add per-episode duration column to the episodes table

---

## Verification Plan

### Automated Tests
- Unit test `parse_duration()` with all 3 formats + edge cases
- Unit test RSS parsing with a fixture XML file
- Integration test: mock RSS responses, verify duration stored in DB
- `uv run pytest` to confirm all tests pass
- `uv run main.py publish --dry-run` to verify the updated report output

### Manual Verification
- Run `uv run main.py overcast-sync` and check that `duration_seconds` is populated in the DB
- Inspect `SELECT COUNT(*) FROM episodes WHERE duration_seconds IS NOT NULL` vs total episodes
- Review generated markdown for the `Time Listened` line
