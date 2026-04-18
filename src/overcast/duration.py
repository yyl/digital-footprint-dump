"""Parse <itunes:duration> values from podcast RSS feeds."""


from typing import Optional

def parse_duration(value: str) -> Optional[int]:
    """Parse an itunes:duration value to seconds.

    Handles three formats:
      - Raw seconds: "1541"
      - MM:SS: "24:09"
      - HH:MM:SS: "02:31:53"

    Returns:
        Duration in seconds, or None if the value is empty.
        
    Raises:
        ValueError: If the duration string is in an unknown format.
    """
    if not value or not value.strip():
        return None

    value = value.strip()

    # Raw seconds (all digits)
    if value.isdigit():
        return int(value)

    # HH:MM:SS or MM:SS
    parts = value.split(":")
    if len(parts) == 3:
        try:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            return h * 3600 + m * 60 + s
        except ValueError:
            raise ValueError(f"Invalid HH:MM:SS duration format: '{value}'")
    elif len(parts) == 2:
        try:
            m, s = int(parts[0]), int(parts[1])
            return m * 60 + s
        except ValueError:
            raise ValueError(f"Invalid MM:SS duration format: '{value}'")

    raise ValueError(f"Unknown duration format: '{value}'")
