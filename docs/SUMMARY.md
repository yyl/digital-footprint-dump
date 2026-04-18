# Report Summary Format

This document details the exact contents, layout, and output format for the generated monthly reports.

## Overview

The `publish` command generates a monthly activity report as a draft Hugo post and commits it to a GitHub-hosted blog.
It chooses the latest available `YYYY-MM` across all analysis databases that are present, so optional sources can be missing without blocking report generation.

## Report Output Format

- **Post title format:** `Wrap up {month_name} {year}`
- **Post slug format:** `wrap-up-{month}-{year}`
- **Post file format:** `content/posts/wrap-up-{month}-{year}.md`
- **Draft status:** Posts are committed as drafts (`draft: true`)

## Report Contents

- A "What's new" section right below the front matter dynamically populated with newly discovered reading sources, podcast feeds, and GitHub repos.
- Keeps the existing top-level metrics, including Month-over-Month (MoM) and Year-over-Year (YoY) comparisons.
- **Readwise (Articles):** Adds a ranked Readwise source summary table, then per-source article tables using the same grouping rule: sources with more than one article get their own section and one-off sources roll into `Other`. First-time sources are highlighted with a 🆕 emoji and get their own standalone row in the summary table.
- **Readwise (Newsletters):** Skips broken Readwise newsletter-style `mailto:` links and renders those titles as plain text.
- **Readwise (Highlights):** Adds Readwise highlights as grouped quote-style entries with date and note metadata.
- **Movies (Letterboxd):** Adds movie tables with watch date and rating.
- **Podcasts (Overcast):** Adds podcast summaries ranked by episode count, followed by grouped episode tables using the same `Other` bucketing rule for one-off podcasts. Newly subscribed feeds are highlighted with a 🆕 emoji and get their own standalone row in the summary table.
- **GitHub Commits:** Adds GitHub repo summaries ranked by commit count, followed by grouped commit tables using the same `Other` bucketing rule for one-off repos, with merge PR commits (`Merge pull request #`) excluded.
