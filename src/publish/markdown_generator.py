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
        
        return f"""---
title: "{title}"
date: {date_iso}
draft: true
tags: ["monthly", "readwise", "digest", "automated"]
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
