"""Markdown generator for Hugo-compatible blog articles."""

from datetime import datetime
from typing import Dict, Any
from zoneinfo import ZoneInfo


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
        title = f"Monthly activity summary - {month}/{year}"
        
        # Use current time in PDT for the date
        pdt = ZoneInfo("America/Los_Angeles")
        now = datetime.now(pdt)
        date_iso = now.isoformat(timespec='seconds')
        
        # Build tags based on available data
        tags = ["monthly", "digest", "automated"]
        if data.get('readwise'):
            tags.append("readwise")
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
        
        return f"""
## Readwise

- **Articles Archived**: {articles}
- **Total Words Read**: {words:,}
- **Time Spent Reading**: {time_display}
- **Average Reading Speed**: {speed_display}
"""
    
    def _generate_letterboxd_section(self, letterboxd_data: Dict[str, Any]) -> str:
        """Generate the Letterboxd statistics section."""
        movies = letterboxd_data.get('movies_watched', 0)
        avg_rating = letterboxd_data.get('avg_rating', 0)
        min_rating = letterboxd_data.get('min_rating', 0)
        max_rating = letterboxd_data.get('max_rating', 0)
        avg_years = letterboxd_data.get('avg_years_since_release', 0)
        
        return f"""
## Letterboxd

- **Movies Watched**: {int(movies)}
- **Average Rating**: {avg_rating:.2f} ⭐
- **Lowest Rating**: {min_rating:.2f} ⭐
- **Highest Rating**: {max_rating:.2f} ⭐
- **Average Years Since Release**: {avg_years:.2f}
"""
    
    def _generate_overcast_section(self, overcast_data: Dict[str, Any]) -> str:
        """Generate the Overcast/Podcast statistics section."""
        feeds_added = int(overcast_data.get('feeds_added', 0))
        feeds_removed = int(overcast_data.get('feeds_removed', 0))
        episodes_played = int(overcast_data.get('episodes_played', 0))
        
        return f"""
## Podcast (Overcast)

- **New Feeds Subscribed**: {feeds_added}
- **Feeds Removed**: {feeds_removed}
- **Episodes Played**: {episodes_played}
"""
