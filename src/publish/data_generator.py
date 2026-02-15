"""Generator for Hugo-compatible YAML data files from analysis databases."""

import logging
from typing import Dict, List, Optional, Any

from ..readwise.database import ReadwiseDatabase
from ..foursquare.database import FoursquareDatabase
from ..letterboxd.database import LetterboxdDatabase
from ..overcast.database import OvercastDatabase
from ..strong.database import StrongDatabase

logger = logging.getLogger(__name__)


def _to_yaml(records: List[Dict[str, Any]], comment: str) -> str:
    """Serialize a list of flat dicts to YAML list format.
    
    Produces output like:
        # comment
        - month: "2025-08"
          key: value
    
    Args:
        records: List of dictionaries to serialize.
        comment: Comment line at the top of the file.
    
    Returns:
        YAML-formatted string.
    """
    lines = [f"# {comment}"]
    
    for record in records:
        first = True
        for key, value in record.items():
            prefix = "- " if first else "  "
            first = False
            
            # Format values
            if isinstance(value, str):
                formatted = f'"{value}"'
            elif isinstance(value, float):
                formatted = f"{value:.2f}"
            else:
                formatted = str(value)
            
            lines.append(f"{prefix}{key}: {formatted}")
        lines.append("")
    
    return "\n".join(lines) + "\n"


class DataGenerator:
    """Generates Hugo data files from analysis databases."""
    
    def __init__(
        self,
        readwise_db: Optional[ReadwiseDatabase] = None,
        foursquare_db: Optional[FoursquareDatabase] = None,
        letterboxd_db: Optional[LetterboxdDatabase] = None,
        overcast_db: Optional[OvercastDatabase] = None,
        strong_db: Optional[StrongDatabase] = None,
    ):
        """Initialize data generator.
        
        Args:
            readwise_db: Readwise database manager.
            foursquare_db: Foursquare database manager.
            letterboxd_db: Letterboxd database manager.
            overcast_db: Overcast database manager.
            strong_db: Strong database manager.
        """
        self.readwise_db = readwise_db or ReadwiseDatabase()
        self.foursquare_db = foursquare_db or FoursquareDatabase()
        self.letterboxd_db = letterboxd_db or LetterboxdDatabase()
        self.overcast_db = overcast_db or OvercastDatabase()
        self.strong_db = strong_db or StrongDatabase()
    
    def _get_all_readwise(self) -> List[Dict[str, Any]]:
        """Get all Readwise analysis records, oldest first."""
        query = """
        SELECT year_month, articles, words, reading_time_mins
        FROM analysis
        ORDER BY year_month ASC
        """
        with self.readwise_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        
        records = []
        for row in rows:
            row = dict(row)
            words = row['words']
            time_mins = row['reading_time_mins']
            avg_speed = round(words / time_mins) if time_mins and time_mins > 0 else 0
            records.append({
                'month': row['year_month'],
                'articles_archived': row['articles'],
                'total_words': words,
                'time_spent_minutes': time_mins,
                'avg_reading_speed': avg_speed,
            })
        return records
    
    def _get_all_foursquare(self) -> List[Dict[str, Any]]:
        """Get all Foursquare analysis records, oldest first."""
        query = """
        SELECT year_month, checkins, unique_places
        FROM analysis
        ORDER BY year_month ASC
        """
        try:
            with self.foursquare_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            return [
                {
                    'month': dict(row)['year_month'],
                    'checkins': dict(row)['checkins'],
                    'unique_places': dict(row)['unique_places'],
                }
                for row in rows
            ]
        except Exception:
            return []
    
    def _get_all_letterboxd(self) -> List[Dict[str, Any]]:
        """Get all Letterboxd analysis records, oldest first."""
        query = """
        SELECT year_month, movies_watched, avg_rating
        FROM analysis
        ORDER BY year_month ASC
        """
        with self.letterboxd_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        
        return [
            {
                'month': dict(row)['year_month'],
                'movies_watched': dict(row)['movies_watched'],
                'avg_rating': dict(row)['avg_rating'],
            }
            for row in rows
        ]
    
    def _get_all_overcast(self) -> List[Dict[str, Any]]:
        """Get all Overcast analysis records, oldest first."""
        if not self.overcast_db.exists():
            return []
        
        query = """
        SELECT year_month, feeds_added, feeds_removed, episodes_played
        FROM analysis
        ORDER BY year_month ASC
        """
        try:
            with self.overcast_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            return [
                {
                    'month': dict(row)['year_month'],
                    'feeds_added': dict(row)['feeds_added'],
                    'feeds_removed': dict(row)['feeds_removed'],
                    'episodes_played': dict(row)['episodes_played'],
                }
                for row in rows
            ]
        except Exception:
            return []
    
    def _get_all_strong(self) -> List[Dict[str, Any]]:
        """Get all Strong analysis records, oldest first."""
        if not self.strong_db.exists():
            return []
        
        query = """
        SELECT year_month, workouts, total_minutes, unique_exercises, total_sets
        FROM analysis
        ORDER BY year_month ASC
        """
        try:
            with self.strong_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
            
            return [
                {
                    'month': dict(row)['year_month'],
                    'workouts': dict(row)['workouts'],
                    'total_minutes': dict(row)['total_minutes'],
                    'unique_exercises': dict(row)['unique_exercises'],
                    'total_sets': dict(row)['total_sets'],
                }
                for row in rows
            ]
        except Exception:
            return []
    
    def generate_data_files(self) -> Dict[str, str]:
        """Generate all Hugo data files.
        
        Returns:
            Dictionary mapping repo file paths to YAML content strings.
            Example: {"data/activity/reading.yaml": "# Monthly reading..."}
        """
        files = {}
        
        # Reading (Readwise)
        reading_records = self._get_all_readwise()
        if reading_records:
            files["data/activity/reading.yaml"] = _to_yaml(
                reading_records, "Monthly reading activity data"
            )
            logger.info(f"Generated reading.yaml with {len(reading_records)} records")
        
        # Travel (Foursquare)
        travel_records = self._get_all_foursquare()
        if travel_records:
            files["data/activity/travel.yaml"] = _to_yaml(
                travel_records, "Monthly travel activity data"
            )
            logger.info(f"Generated travel.yaml with {len(travel_records)} records")
        
        # Movies (Letterboxd)
        movies_records = self._get_all_letterboxd()
        if movies_records:
            files["data/activity/movies.yaml"] = _to_yaml(
                movies_records, "Monthly movies activity data"
            )
            logger.info(f"Generated movies.yaml with {len(movies_records)} records")
        
        # Podcasts (Overcast)
        podcasts_records = self._get_all_overcast()
        if podcasts_records:
            files["data/activity/podcasts.yaml"] = _to_yaml(
                podcasts_records, "Monthly podcasts activity data"
            )
            logger.info(f"Generated podcasts.yaml with {len(podcasts_records)} records")
        
        # Workouts (Strong)
        workouts_records = self._get_all_strong()
        if workouts_records:
            files["data/activity/workouts.yaml"] = _to_yaml(
                workouts_records, "Monthly workout activity data"
            )
            logger.info(f"Generated workouts.yaml with {len(workouts_records)} records")
        
        logger.info(f"Generated {len(files)} data files total")
        return files
