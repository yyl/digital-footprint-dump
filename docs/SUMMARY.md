# Report Summary Format

This document details the exact contents, layout, and output format for the generated monthly reports.

## Overview

The `publish` command generates a monthly activity report as a draft Hugo post and commits it to a GitHub-hosted blog.
It chooses the latest available `YYYY-MM` across all analysis databases that are present, so optional sources can be missing without blocking report generation.

## Report Output Format

- **Post title format:** `Things I learned in {month}/{year}`
- **Post slug format:** `things-i-learned-in-{month}-{year}`
- **Post file format:** `content/posts/{year}-{month}-monthly-report.md`
- **Draft status:** Posts are committed as drafts (`draft: true`)

## Report Contents

- Keeps the existing top-level metrics, including Month-over-Month (MoM) and Year-over-Year (YoY) comparisons.
- **Readwise (Articles):** Adds a ranked Readwise source summary table, then per-source article tables using the same grouping rule: sources with more than one article get their own section and one-off sources roll into `Other`.
- **Readwise (Newsletters):** Skips broken Readwise newsletter-style `mailto:` links and renders those titles as plain text.
- **Readwise (Highlights):** Adds Readwise highlights as grouped quote-style entries with date and note metadata.
- **Movies (Letterboxd):** Adds movie tables with watch date and rating.
- **Podcasts (Overcast):** Adds podcast summaries ranked by episode count, followed by grouped episode tables using the same `Other` bucketing rule for one-off podcasts.
- **GitHub Commits:** Adds GitHub repo summaries ranked by commit count, followed by grouped commit tables using the same `Other` bucketing rule for one-off repos, with merge-PR commits excluded.

## Implementation Details

- GitHub publishing uses PyGithub for authenticated write operations.
- If the target branch moves during publish, the GitHub client automatically retries non-fast-forward ref update failures.
- GitHub activity sync uses an inclusive timestamp cursor plus SHA de-duplication so same-second commits are not skipped during incremental sync.
