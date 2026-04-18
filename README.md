# digital-footprint-dump

[![Tests](https://github.com/yyl/digital-footprint-dump/actions/workflows/tests.yml/badge.svg)](https://github.com/yyl/digital-footprint-dump/actions/workflows/tests.yml)

A pipeline to fetch data from digital sources, analyze them, and publish a monthly draft report to a markdown blog site.

## Setup

```bash
uv python install $(cat .python-version)
uv sync
cp .env.example .env
# Edit .env with your credentials
```

The repo pins its expected Python version in `.python-version`. CI and the recommended local test flow both use that exact version for consistency.

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize all databases |
| `sync` | Sync all services |
| `analyze` | Analyze all sources |
| `publish` | Generate and commit a monthly draft report blog post |
| `backfill` | Commit activity data files to blog repo |
| `status` | Show sync status |
| `{source}-sync` | Sync a specific source |
| `{source}-analyze` | Analyze a specific source |

Run with: `uv run main.py <command>`

See [docs/SOURCES.md](docs/SOURCES.md) for details on supported sources (`readwise`, `foursquare`, `letterboxd`, `overcast`, `strong`, `apple-health`, `blog`, `hardcover`, `github`).

`sync`/`{source}-sync` create or refresh raw source data only. Monthly `analysis` tables are created when you run `analyze`, `{source}-analyze`, or `publish`. (Note: `overcast-sync` also performs an active network fetch to pull missing episode durations from live RSS feeds).

For specific details on tests, database definitions, module structure, storage and cloud deployment, see [src/README.md](src/README.md).

### Publishing

The pipeline generates a markdown report from the local SQLite databases. See [docs/SUMMARY.md](docs/SUMMARY.md) for details on the report format and logic.

**Commands:**
- `publish`: Syncs latest data, runs analysis, generates markdown, and commits the draft report post to GitHub.
- `publish --skip-sync-analysis`: Generates and commits the draft report post using the current analysis data without rerunning sync or analysis.
- `publish --dry-run`: Generates the markdown locally from the current analysis data without syncing or publishing anything.
- `publish --last-month`: Generates and commits the report for the previous month instead of the latest month.

**Required in .env:**
- `BLOG_GITHUB_TOKEN` - Fine-grained PAT scoped to blog repo with **Contents: Read and write** permission
- `BLOG_REPO_OWNER` - Repository owner username
- `BLOG_REPO_NAME` - Repository name
- `BLOG_GITHUB_TARGET_BRANCH` - (optional) Branch to commit to, defaults to `main`

**Optional blog tracking config:**
- `BLOG_POSTS_INDEX_URL` - Public Hugo JSON export for published posts, defaults to `https://www.mildlyjournaling.com/posts/index.json`

### GitHub Actions Workflow

This project includes a GitHub Action (`monthly-pipeline.yml`) to automatically or manually run the pipeline. For detailed setup instructions (secrets, private repo definitions), see [src/README.md](src/README.md).

**Schedule:**
The workflow runs automatically on the **last day of each month at 11:00 AM UTC**.

**Manual Trigger:**
1. Go to **Actions** tab in your repository
2. Select **"Monthly Pipeline"** workflow
3. Click **"Run workflow"**
4. Optional flags like `Publish for the last month` or `dry-run` are available in the prompt.
