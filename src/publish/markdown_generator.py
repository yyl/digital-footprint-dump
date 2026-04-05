"""Markdown generator for Hugo-compatible blog articles."""

from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo
from urllib.parse import quote, urlparse

from ..comparison import format_change, format_comparison_suffix


class MarkdownGenerator:
    """Generates Hugo-compatible markdown content for monthly summaries."""
    
    def generate_monthly_summary(self, data: Dict[str, Any]) -> str:
        """Generate complete markdown content for the monthly summary.
        
        Args:
            data: Dictionary with 'year', 'month', and source-specific data.
            
        Returns:
            Complete markdown content as string.
        """
        parts = []
        
        # Front matter
        parts.append(self._generate_front_matter(data))
        
        # Readwise section
        if data.get('readwise'):
            parts.append(self._generate_readwise_section(data['readwise']))
        
        # Foursquare section
        if data.get('foursquare'):
            parts.append(self._generate_foursquare_section(data['foursquare']))
        
        # Letterboxd section
        if data.get('letterboxd'):
            parts.append(self._generate_letterboxd_section(data['letterboxd']))
        
        # Overcast section
        if data.get('overcast'):
            parts.append(self._generate_overcast_section(data['overcast']))
        
        # Strong section
        if data.get('strong'):
            parts.append(self._generate_strong_section(data['strong']))
        
        # Hardcover section
        if data.get('hardcover'):
            parts.append(self._generate_hardcover_section(data['hardcover']))
        
        # GitHub section
        if data.get('github'):
            parts.append(self._generate_github_section(data['github']))
        
        return "\n".join(parts)
    
    def _generate_front_matter(self, data: Dict[str, Any]) -> str:
        """Generate YAML front matter for the markdown file."""
        month = data['month']
        year = data['year']
        title = f"Things I learned in {month}/{year}"
        slug = f"things-i-learned-in-{month}-{year}"
        
        # Use current time in PDT for the date
        pdt = ZoneInfo("America/Los_Angeles")
        now = datetime.now(pdt)
        date_iso = now.isoformat(timespec='seconds')
        
        # Build tags based on available data
        tags = ["monthly", "digest", "automated"]
        if data.get('readwise'):
            tags.append("readwise")
        if data.get('foursquare'):
            tags.append("foursquare")
        if data.get('letterboxd'):
            tags.append("letterboxd")
        if data.get('overcast'):
            tags.append("overcast")
        if data.get('strong'):
            tags.append("strong")
        if data.get('hardcover'):
            tags.append("hardcover")
        if data.get('github'):
            tags.append("github")
        
        tags_str = ", ".join(f'"{t}"' for t in tags)
        
        return f"""---
title: "{title}"
slug: "{slug}"
date: {date_iso}
draft: true
tags: [{tags_str}]
categories: ["Summary"]
---"""
    
    def _generate_readwise_section(self, readwise_data: Dict[str, Any]) -> str:
        """Generate the Readwise statistics section."""
        articles = readwise_data.get('articles', 0)
        words = readwise_data.get('words', 0)
        reading_time_mins = readwise_data.get('reading_time_mins', 0)
        comparisons = readwise_data.get('comparisons', {})
        
        # Format time spent reading
        if reading_time_mins < 60:
            time_display = f"{reading_time_mins} minutes"
        else:
            hours = reading_time_mins // 60
            minutes = reading_time_mins % 60
            time_display = f"{hours}h {minutes}m"
        
        # Calculate average reading speed (words per minute)
        if reading_time_mins > 0:
            avg_speed = round(words / reading_time_mins)
            speed_display = f"{avg_speed:,} words/min"
        else:
            speed_display = "N/A"
        
        # Format comparison strings
        articles_comparison = format_comparison_suffix(comparisons.get('articles'))
        words_comparison = format_comparison_suffix(comparisons.get('words'))
        time_comparison = format_comparison_suffix(comparisons.get('reading_time_mins'))
        
        # Compute average reading speed comparison
        # Speed = words / time, so if both words and time change, speed change is derived
        speed_comparison = self._compute_speed_comparison(comparisons)
        
        # Per-article word count stats
        max_wpa = readwise_data.get('max_words_per_article', 0)
        median_wpa = readwise_data.get('median_words_per_article', 0)
        min_wpa = readwise_data.get('min_words_per_article', 0)
        
        return f"""
## Reading

- **Articles Archived**: {articles}{articles_comparison}
- **Total Words Read**: {words:,}{words_comparison}
- **Time Spent Reading**: {time_display}{time_comparison}
- **Average Reading Speed**: {speed_display}{speed_comparison}
- **Max Words (single article)**: {max_wpa:,}
- **Median Words (per article)**: {median_wpa:,}
- **Min Words (single article)**: {min_wpa:,}
{self._generate_readwise_articles_block(readwise_data.get('article_list', []))}
{self._generate_readwise_highlights_block(readwise_data.get('highlight_groups', []))}
"""
    
    def _compute_speed_comparison(self, comparisons: Dict[str, Any]) -> str:
        """Compute reading speed comparison from words and time comparisons.
        
        Speed = words / time, so percentage change in speed is approximately:
        (1 + words_change) / (1 + time_change) - 1
        """
        if not comparisons:
            return ""
        
        words_changes = comparisons.get('words', {})
        time_changes = comparisons.get('reading_time_mins', {})
        
        def compute_speed_change(words_pct: Optional[float], time_pct: Optional[float]) -> Optional[float]:
            if words_pct is None or time_pct is None:
                return None
            # Convert percentages back to ratios
            words_ratio = 1 + (words_pct / 100)
            time_ratio = 1 + (time_pct / 100)
            if time_ratio == 0:
                return None
            speed_ratio = words_ratio / time_ratio
            return round((speed_ratio - 1) * 100, 1)
        
        speed_mom = compute_speed_change(words_changes.get('mom'), time_changes.get('mom'))
        speed_yoy = compute_speed_change(words_changes.get('yoy'), time_changes.get('yoy'))
        
        return format_comparison_suffix({'mom': speed_mom, 'yoy': speed_yoy})
    
    def _generate_foursquare_section(self, foursquare_data: Dict[str, Any]) -> str:
        """Generate the Foursquare statistics section."""
        checkins = int(foursquare_data.get('checkins', 0))
        unique_places = int(foursquare_data.get('unique_places', 0))
        comparisons = foursquare_data.get('comparisons', {})
        
        checkins_cmp = format_comparison_suffix(comparisons.get('checkins'))
        places_cmp = format_comparison_suffix(comparisons.get('unique_places'))
        
        return f"""
## Travel

- **Checkins**: {checkins}{checkins_cmp}
- **Unique Places Visited**: {unique_places}{places_cmp}
"""
    
    def _generate_letterboxd_section(self, letterboxd_data: Dict[str, Any]) -> str:
        """Generate the Letterboxd statistics section."""
        movies = letterboxd_data.get('movies_watched', 0)
        avg_rating = letterboxd_data.get('avg_rating', 0)
        min_rating = letterboxd_data.get('min_rating', 0)
        max_rating = letterboxd_data.get('max_rating', 0)
        avg_years = letterboxd_data.get('avg_years_since_release', 0)
        comparisons = letterboxd_data.get('comparisons', {})
        
        movies_cmp = format_comparison_suffix(comparisons.get('movies_watched'))
        rating_cmp = format_comparison_suffix(comparisons.get('avg_rating'))
        
        return f"""
## Movies

- **Movies Watched**: {int(movies)}{movies_cmp}
- **Average Rating**: {avg_rating:.2f} ⭐{rating_cmp}
- **Lowest Rating**: {min_rating:.2f} ⭐
- **Highest Rating**: {max_rating:.2f} ⭐
- **Average Years Since Release**: {avg_years:.2f}
{self._generate_movies_block(letterboxd_data.get('movies', []))}
"""
    
    def _generate_overcast_section(self, overcast_data: Dict[str, Any]) -> str:
        """Generate the Overcast/Podcast statistics section."""
        feeds_added = int(overcast_data.get('feeds_added', 0))
        feeds_removed = int(overcast_data.get('feeds_removed', 0))
        episodes_played = int(overcast_data.get('episodes_played', 0))
        comparisons = overcast_data.get('comparisons', {})
        
        played_cmp = format_comparison_suffix(comparisons.get('episodes_played'))
        
        return f"""
## Podcasts

- **New Feeds Subscribed**: {feeds_added}
- **Feeds Removed**: {feeds_removed}
- **Episodes Played**: {episodes_played}{played_cmp}
{self._generate_podcasts_block(overcast_data.get('episodes', []))}
"""
    
    def _generate_strong_section(self, strong_data: Dict[str, Any]) -> str:
        """Generate the Strong/Workout statistics section."""
        workouts = int(strong_data.get('workouts', 0))
        total_minutes = int(strong_data.get('total_minutes', 0))
        unique_exercises = int(strong_data.get('unique_exercises', 0))
        total_sets = int(strong_data.get('total_sets', 0))
        comparisons = strong_data.get('comparisons', {})
        
        # Format time
        if total_minutes < 60:
            time_display = f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            time_display = f"{hours}h {minutes}m"
        
        workouts_cmp = format_comparison_suffix(comparisons.get('workouts'))
        time_cmp = format_comparison_suffix(comparisons.get('total_minutes'))
        
        return f"""
## Workout

- **Workouts**: {workouts}{workouts_cmp}
- **Total Time**: {time_display}{time_cmp}
- **Unique Exercises**: {unique_exercises}
- **Total Sets**: {total_sets}
"""
    
    def _generate_hardcover_section(self, hardcover_data: Dict[str, Any]) -> str:
        """Generate the Hardcover/Books statistics section."""
        books = int(hardcover_data.get('books_finished', 0))
        avg_rating = hardcover_data.get('avg_rating', 0)
        comparisons = hardcover_data.get('comparisons', {})
        
        books_cmp = format_comparison_suffix(comparisons.get('books_finished'))
        rating_cmp = format_comparison_suffix(comparisons.get('avg_rating'))
        
        return f"""
## Books

- **Books Finished**: {books}{books_cmp}
- **Average Rating**: {avg_rating:.2f} ⭐{rating_cmp}
"""
    
    def _generate_github_section(self, github_data: Dict[str, Any]) -> str:
        """Generate the GitHub/Code statistics section."""
        commits = int(github_data.get('commits', 0))
        repos_touched = int(github_data.get('repos_touched', 0))
        comparisons = github_data.get('comparisons', {})
        
        commits_cmp = format_comparison_suffix(comparisons.get('commits'))
        repos_cmp = format_comparison_suffix(comparisons.get('repos_touched'))
        
        return f"""
## Code

- **Commits**: {commits}{commits_cmp}
- **Repos Touched**: {repos_touched}{repos_cmp}
{self._generate_commit_groups_block(github_data.get('commit_groups', []))}
"""

    def _generate_readwise_articles_block(self, articles: list[Dict[str, Any]]) -> str:
        """Generate the archived article list block."""
        if not articles:
            return ""

        source_counts: dict[str, int] = {}
        for article in articles:
            source_name = (article.get('site_name') or "").strip() or "Other"
            source_counts[source_name] = source_counts.get(source_name, 0) + 1

        grouped_counts: dict[str, int] = {}
        grouped: dict[str, list[Dict[str, Any]]] = {}
        for article in articles:
            source_name = (article.get('site_name') or "").strip() or "Other"
            group_name = source_name if source_counts.get(source_name, 0) > 1 else "Other"
            grouped_counts[group_name] = grouped_counts.get(group_name, 0) + 1
            grouped.setdefault(group_name, []).append(article)

        ordered_group_names = self._ordered_group_names(grouped_counts)

        lines = ["", "### Articles Read"]
        lines.extend([
            "",
            "| Source | Articles |",
            "| --- | --- |",
        ])
        for source_name, count in self._sorted_group_counts(grouped_counts):
            lines.append(f"| {self._escape_table_text(source_name)} | {count} |")

        for group_name in ordered_group_names:
            show_source_column = group_name == "Other"
            lines.extend([
                "",
                f"#### {self._escape_table_text(group_name)}",
                "",
                "| Date | Article | Speed | Source |" if show_source_column else "| Date | Article | Speed |",
                "| --- | --- | --- | --- |" if show_source_column else "| --- | --- | --- |",
            ])
            for article in grouped[group_name]:
                title = article.get('title') or "Untitled"
                link = article.get('link')
                label = self._markdown_link(title, link)
                date = self._format_date(article.get('last_moved_at'))
                speed = self._format_speed(article.get('reading_speed_wpm'))
                source = self._escape_table_text((article.get('site_name') or "").strip())
                if show_source_column:
                    lines.append(f"| {date} | {label} | {speed} | {source} |")
                else:
                    lines.append(f"| {date} | {label} | {speed} |")
        return "\n".join(lines)

    def _generate_readwise_highlights_block(self, highlight_groups: list[Dict[str, Any]]) -> str:
        """Generate grouped Readwise highlights."""
        if not highlight_groups:
            return ""

        lines = ["", "### Highlights"]
        for group in highlight_groups:
            title = group.get('title') or "Untitled"
            category = group.get('category')
            heading = self._markdown_link(title, group.get('link'))
            if category:
                heading = f"{heading} ({category})"
            lines.extend([
                "",
                f"#### {heading}",
            ])
            for highlight in group.get('highlights', []):
                lines.extend(self._format_readwise_highlight(highlight))
        return "\n".join(lines)

    def _generate_movies_block(self, movies: list[Dict[str, Any]]) -> str:
        """Generate the watched movies list block."""
        if not movies:
            return ""

        lines = [
            "",
            "### Movies Watched",
            "",
            "| Date | Movie | Rating |",
            "| --- | --- | --- |",
        ]
        for movie in movies:
            title = movie.get('movie_name') or "Untitled"
            year = movie.get('year')
            rating = movie.get('rating')
            watched_at = movie.get('watched_at')
            label = self._markdown_link(title, movie.get('letterboxd_uri'))
            if year:
                label = f"{label} ({year})"
            rating_display = f"{float(rating):.2f} ⭐" if rating is not None else ""
            lines.append(
                f"| {self._format_date(watched_at)} | {label} | {self._escape_table_text(rating_display)} |"
            )
        return "\n".join(lines)

    def _generate_podcasts_block(self, episodes: list[Dict[str, Any]]) -> str:
        """Generate podcasts and episode list block."""
        if not episodes:
            return ""

        podcast_counts: dict[str, int] = {}
        for episode in episodes:
            podcast_title = episode.get('podcast_title') or "Unknown podcast"
            podcast_counts[podcast_title] = podcast_counts.get(podcast_title, 0) + 1

        grouped_counts: dict[str, int] = {}
        grouped: dict[str, list[Dict[str, Any]]] = {}
        podcast_links: dict[str, Optional[str]] = {}
        for episode in episodes:
            podcast_title = episode.get('podcast_title') or "Unknown podcast"
            group_name = podcast_title if podcast_counts.get(podcast_title, 0) > 1 else "Other"
            grouped_counts[group_name] = grouped_counts.get(group_name, 0) + 1
            grouped.setdefault(group_name, []).append(episode)
            if group_name != "Other":
                podcast_links[group_name] = episode.get('podcast_link')

        lines = ["", "### Episodes Listened", "", "| Podcast | Episodes |", "| --- | --- |"]
        for podcast_title, count in self._sorted_group_counts(grouped_counts):
            lines.append(f"| {self._escape_table_text(podcast_title)} | {count} |")

        for podcast_title in self._ordered_group_names(grouped_counts):
            grouped_episodes = grouped[podcast_title]
            podcast_link = podcast_links.get(podcast_title)
            lines.extend([
                "",
                f"#### {self._markdown_link(podcast_title, podcast_link)}",
                "",
                "| Date | Episode | Podcast |" if podcast_title == "Other" else "| Date | Episode |",
                "| --- | --- | --- |" if podcast_title == "Other" else "| --- | --- |",
            ])
            for episode in grouped_episodes:
                episode_title = episode.get('episode_title') or "Untitled episode"
                episode_link = episode.get('episode_link')
                episode_part = self._markdown_link(episode_title, episode_link)
                if podcast_title == "Other":
                    source = self._escape_table_text(episode.get('podcast_title') or "Unknown podcast")
                    lines.append(
                        f"| {self._format_date(episode.get('userUpdatedDate'))} | {episode_part} | {source} |"
                    )
                else:
                    lines.append(
                        f"| {self._format_date(episode.get('userUpdatedDate'))} | {episode_part} |"
                    )
        return "\n".join(lines)

    def _generate_commit_groups_block(self, commit_groups: list[Dict[str, Any]]) -> str:
        """Generate commit list grouped by repository."""
        if not commit_groups:
            return ""

        repo_counts: dict[str, int] = {}
        grouped: dict[str, list[Dict[str, Any]]] = {}
        repo_urls: dict[str, str] = {}
        for group in commit_groups:
            repo = group.get('repo') or "unknown"
            commits = group.get('commits', [])
            group_name = repo if len(commits) > 1 else "Other"
            repo_counts[group_name] = repo_counts.get(group_name, 0) + len(commits)
            grouped.setdefault(group_name, []).extend(commits)
            if group_name != "Other":
                repo_urls[group_name] = f"https://github.com/{quote(repo, safe='/')}"

        lines = ["", "### Commits by Repo", "", "| Repo | Commits |", "| --- | --- |"]
        for repo, count in self._sorted_group_counts(repo_counts):
            lines.append(f"| {self._escape_table_text(repo)} | {count} |")

        for repo in self._ordered_group_names(repo_counts):
            repo_url = repo_urls.get(repo)
            lines.extend([
                "",
                f"#### {self._markdown_link(repo, repo_url)}",
                "",
                "| Date | Commit Message | Repo |" if repo == "Other" else "| Date | Commit Message |",
                "| --- | --- | --- |" if repo == "Other" else "| --- | --- |",
            ])
            for commit in grouped[repo]:
                message = self._escape_table_text(
                    self._clean_text(commit.get('message')) or "(no message)"
                )
                if repo == "Other":
                    source_repo = self._escape_table_text(commit.get('repo') or "unknown")
                    lines.append(
                        f"| {self._format_date(commit.get('author_date'))} | {message} | {source_repo} |"
                    )
                else:
                    lines.append(f"| {self._format_date(commit.get('author_date'))} | {message} |")
        return "\n".join(lines)

    def _markdown_link(self, label: str, url: Optional[str]) -> str:
        """Format a markdown link when a URL is available."""
        safe_label = self._escape_table_text(
            self._clean_text(label).replace("[", "\\[").replace("]", "\\]")
        )
        if self._is_linkable_url(url):
            return f"[{safe_label}]({url})"
        return safe_label

    def _is_linkable_url(self, url: Optional[str]) -> bool:
        """Return True when a URL should be rendered as a clickable markdown link."""
        if not url:
            return False

        parsed = urlparse(str(url).strip())
        return parsed.scheme.lower() != "mailto"

    def _sorted_group_counts(self, group_counts: dict[str, int]) -> list[tuple[str, int]]:
        """Return grouped counts sorted by count descending, with Other last on ties."""
        return sorted(
            group_counts.items(),
            key=lambda item: (-item[1], item[0] == "Other", item[0].lower())
        )

    def _ordered_group_names(self, group_counts: dict[str, int]) -> list[str]:
        """Return group names ordered consistently with the summary ranking."""
        return [name for name, _ in self._sorted_group_counts(group_counts)]

    def _clean_text(self, value: Optional[str]) -> str:
        """Normalize multiline content for markdown bullet lists."""
        if not value:
            return ""
        return " ".join(str(value).split())

    def _escape_table_text(self, value: Optional[str]) -> str:
        """Escape content so it renders safely inside markdown tables."""
        if not value:
            return ""
        return str(value).replace("|", "\\|")

    def _format_date(self, value: Optional[str]) -> str:
        """Format timestamps consistently for report tables."""
        if not value:
            return ""
        return str(value)[:10]

    def _format_speed(self, value: Optional[int]) -> str:
        """Format reading speed for article tables."""
        if value is None:
            return ""
        return f"{int(value)} wpm"

    def _format_readwise_highlight(self, highlight: Dict[str, Any]) -> list[str]:
        """Format a single Readwise highlight as a quote-style markdown block."""
        text = self._clean_text(highlight.get('text'))
        note = self._clean_text(highlight.get('note'))
        date = self._format_date(highlight.get('date'))

        lines = [""]
        if text:
            lines.append(f"> {text}")
        if note:
            lines.append(">")
            lines.append(f"> Note: {note}")
        if date:
            lines.append("")
            lines.append(f"*{date}*")
        return lines
