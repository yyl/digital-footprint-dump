"""Shared helpers for timezone-aware timestamps."""

from datetime import datetime, UTC


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string with a trailing Z."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
