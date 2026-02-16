"""Markdown generator for Hugo-compatible blog articles."""

from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

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
        
        return "\n".join(parts)
    
    def _generate_front_matter(self, data: Dict[str, Any]) -> str:
        """Generate YAML front matter for the markdown file."""
        month = data['month']
        year = data['year']
        title = f"What did I do this month - {month}/{year} edition"
        
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
        
        tags_str = ", ".join(f'"{t}"' for t in tags)
        
        return f"""---
title: "{title}"
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
"""
