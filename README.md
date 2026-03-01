# digital-footprint-dump

A pipeline to fetch data from digital sources, analyze them, and publish monthly summary to a markdown blog site.

## Setup

```bash
uv sync
cp .env.example .env
# Edit .env with your credentials
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize all databases |
| `sync` | Sync all services |
| `analyze` | Analyze all sources |
| `publish` | Publish monthly summary blog post |
| `backfill` | Commit activity data files to blog repo |
| `status` | Show sync status |
| `{source}-sync` | Sync a specific source |
| `{source}-analyze` | Analyze a specific source |

**Supported sources:** `readwise`, `foursquare`, `letterboxd`, `overcast`, `strong`, `hardcover`, `github`

Run with: `uv run main.py <command>`

---

## Readwise

Exports books, highlights, and Reader documents to `data/readwise.db`.

**Commands:**
- `readwise-sync`: Syncs data from Readwise API to the local database.
- `readwise-analyze`: Generates monthly reading stats (archived articles, total words, reading time, max/median/min words per article) and writes to the `analysis` table in `data/readwise.db`.

**Required in .env:**
- `READWISE_ACCESS_TOKEN` - Get from [readwise.io/access_token](https://readwise.io/access_token)

---

## Foursquare

Exports checkins and places to `data/foursquare.db`.

**Commands:**
- `foursquare-sync`: Syncs checkin history from Foursquare API.
- `foursquare-analyze`: Generates monthly stats (checkins, unique places) and writes to the `analysis` table.

**Required in .env:**
- `FOURSQUARE_ACCESS_TOKEN` - OAuth token used for all v2 API calls (checkins, user info)
- `FOURSQUARE_CLIENT_ID` - Only needed for initial OAuth flow / re-auth. From your [Foursquare app](https://foursquare.com/developers/apps)
- `FOURSQUARE_CLIENT_SECRET` - Only needed for initial OAuth flow / re-auth
- `FOURSQUARE_API_KEY` - *(optional)* Service key for Places API; enriches venue details but falls back to checkin data if absent

---

## Letterboxd

Imports watched movies and ratings from CSV export to `data/letterboxd.db`.

**Commands:**
- `letterboxd-sync`: Imports data from Letterboxd CSV export.
- `letterboxd-analyze`: Generates monthly movie stats (count, avg/min/max rating, avg years since release) and writes to the `analysis` table.

**Setup:**
1. Export your data from [letterboxd.com/settings/data](https://letterboxd.com/settings/data/)
2. Unzip and place folder in `files/` (e.g., `files/letterboxd-username-2025-...`)
3. Run `uv run main.py letterboxd-sync`

---

## Overcast

Imports podcast feeds and episodes from OPML export to `data/overcast.db`.

**Commands:**
- `overcast-sync`: Imports data from Overcast OPML export.
- `overcast-analyze`: Generates monthly podcast stats (feeds added, feeds removed, episodes played) and writes to the `analysis` table.

**Setup:**
1. Export from [overcast.fm/account](https://overcast.fm/account) → "All data" OPML
2. Place file in `files/` (e.g., `files/overcast.opml`)
3. Run `uv run main.py overcast-sync`

---

## Strong

Imports workout data from Strong app CSV export to `data/strong.db`.

**Commands:**
- `strong-sync`: Imports workout and exercise data from CSV export.
- `strong-analyze`: Generates monthly stats (workouts, total minutes, unique exercises, total sets) and writes to the `analysis` table.

**Setup:**
1. Export from [Strong app](https://www.strong.app/) → Settings → Export Data
2. Place CSV in `files/` (e.g., `files/strong_workouts.csv`)
3. Run `uv run main.py strong-sync`

---

## Hardcover

Syncs finished books from [Hardcover](https://hardcover.app/) via their GraphQL API to `data/hardcover.db`.

**Commands:**
- `hardcover-sync`: Fetches all books marked as "read" from Hardcover API.
- `hardcover-analyze`: Generates monthly stats (books finished, average rating) and writes to the `analysis` table.

**Setup:**
1. Get your API token from [hardcover.app/account/api](https://hardcover.app/account/api)
2. Add to `.env`: `HARDCOVER_ACCESS_TOKEN=your_token_here`
3. Run `uv run main.py hardcover-sync`

---

## GitHub

Syncs commit history from your public repositories via the GitHub REST API to `data/github.db`.

**Commands:**
- `github-sync`: Fetches commits from all owned public repos (non-fork).
- `github-analyze`: Generates monthly stats (commits, repos touched) and writes to the `analysis` table.

**Required in .env:**
- `CODEBASE_USERNAME` - Your GitHub username
- `BLOG_GITHUB_TOKEN` - Reused for authenticated API access (5000 req/hr)

---

## Publishing

Publishes a monthly activity summary to a GitHub-hosted Hugo blog.

**Commands:**
- `publish`: Syncs latest data, runs analysis, generates markdown, and commits the blog post to GitHub.
- `backfill`: Syncs latest data, runs analysis, generates Hugo data files (`data/activity/*.yaml`), and commits them to GitHub. These power the Activity page charts.

**Required in .env:**
- `BLOG_GITHUB_TOKEN` - Fine-grained PAT scoped to blog repo with **Contents: Read and write** permission
- `BLOG_REPO_OWNER` - Repository owner username
- `BLOG_REPO_NAME` - Repository name
- `BLOG_GITHUB_TARGET_BRANCH` - (optional) Branch to commit to, defaults to `main`

---

## Cloud Deployment (GitHub Actions)

Automate the pipeline to run monthly using GitHub Actions with a private data repository.

### Setup

1. **Create a private data repository** (e.g., `digital-footprint-data`):
   ```
   digital-footprint-data/
   ├── data/           # Empty initially, DBs auto-created
   └── files/          # Manual exports (Letterboxd, Overcast, Strong)
       ├── letterboxd-export/
       ├── overcast.opml
       └── strong_workouts.csv
   ```

2. **Create two fine-grained Personal Access Tokens** at [github.com/settings/tokens](https://github.com/settings/tokens):

   | Token | Repo scope | Permissions needed |
   |-------|-----------|--------------------|
   | `DATA_REPO_PAT` | Private data repo | **Contents: Read and write** |
   | `BLOG_GITHUB_TOKEN` | Blog repo | **Contents: Read and write** |

   > These can be the same token if it has access to both repos.

3. **Add secrets** to your public repo (Settings → Secrets → Actions):

   | Secret | Description |
   |--------|-------------|
   | `DATA_REPO_OWNER` | Your GitHub username |
   | `DATA_REPO_NAME` | Private data repo name |
   | `DATA_REPO_PAT` | PAT with Contents read/write on data repo |
   | `READWISE_ACCESS_TOKEN` | Readwise API token |
   | `FOURSQUARE_ACCESS_TOKEN` | Foursquare OAuth token — required for all API calls |
   | `FOURSQUARE_API_KEY` | *(optional)* Foursquare Places API for venue details |
   | `BLOG_GITHUB_TOKEN` | PAT with Contents read/write on blog repo |
   | `BLOG_REPO_OWNER` | Blog repo owner |
   | `BLOG_REPO_NAME` | Blog repo name |
   | `BLOG_GITHUB_TARGET_BRANCH` | *(optional)* Branch to commit to, defaults to `main` |

### Schedule

The workflow runs automatically on the **last day of each month at 11:00 AM UTC**.

### Manual Trigger

1. Go to **Actions** tab in your repository
2. Select **"Monthly Pipeline"** workflow
3. Click **"Run workflow"**
4. Optionally enable **dry-run mode** to validate without publishing

### Testing Locally

Validate the workflow with [act](https://github.com/nektos/act):
```bash
act -n  # Dry-run to check syntax
```

Test the dry-run mode:
```bash
uv run main.py publish --dry-run
```

