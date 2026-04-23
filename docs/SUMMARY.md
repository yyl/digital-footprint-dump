# Report Summary Format

This document describes what the generated monthly report looks like.

## Overview

The `publish` command generates a draft markdown wrap-up post for a single month.

The report is built from each source's monthly analysis data and includes the latest available month across the initialized sources, unless `--last-month` is used.

## Output Format

- Title format: `Wrap up {month_name} {year}`
- Slug format: `wrap-up-{month}-{year}`
- Output path: `content/posts/wrap-up-{month}-{year}.md`
- Draft status: `draft: true`

## High-Level Layout

The report contains:

1. Hugo front matter
2. `What's new`
3. `Reading`
4. `Travel`
5. `Movies`
6. `Podcasts`
7. `Workout`
8. `Writing`
9. `Books`
10. `Code`

Only sections with available data are included.

## What's New

The `What's new` section appears near the top of the report and highlights newly seen items for the month, such as:

- new reading sources
- new podcast feeds
- new GitHub repos
- new places visited

## Section Details

### Reading

Shows article totals and reading metrics such as:

- articles archived
- total words
- time spent reading
- average reading speed
- max, median, and min words per article

It also includes:

- a ranked source summary table
- grouped article tables
- grouped highlights

First-time reading sources are marked with `🆕`.

Newsletter-style `mailto:` links are rendered as plain text instead of broken links.

### Travel

Shows:

- checkins
- unique places visited

### Movies

Shows:

- movies watched
- average rating
- min rating
- max rating
- average years since release

It also includes a movie table with watch date and rating for the month.

### Podcasts

Shows:

- new feeds subscribed
- feeds removed
- episodes played
- minutes played

It also includes:

- a ranked podcast summary table
- grouped episode tables

New podcast feeds are marked with `🆕`.

### Workout

Shows:

- workouts
- total time
- total calories

This section is sourced from Apple Health analysis.

### Writing

Shows:

- posts
- total words
- unique tags

It also includes a top-tags table when available.

### Books

Shows:

- books finished
- average rating

### Code

Shows:

- commits
- repos touched

It also includes:

- a ranked repo summary table
- grouped commit tables

Merge commits of the form `Merge pull request #...` are excluded.

## Comparisons

Where enough historical data exists, the report includes:

- Month-over-Month (`MoM`) comparisons
- Year-over-Year (`YoY`) comparisons

These appear inline with top-line metrics.

## Activity Data Files

The related `backfill` workflow regenerates monthly YAML data files under `data/activity/` for the blog.

Those files are not the markdown report itself, but they are derived from the same monthly analysis layer.
