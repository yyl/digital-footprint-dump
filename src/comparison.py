"""Generic utility module for computing MoM/YoY percentage changes."""

from typing import Any, Callable, Dict, List, Optional


def compute_percentage_change(current: float, previous: float) -> Optional[float]:
    """Compute percentage change from previous to current value.
    
    Args:
        current: Current period value.
        previous: Previous period value.
        
    Returns:
        Percentage change as float (e.g., 15.0 for +15%), or None if previous is 0/None.
    """
    if previous is None or previous == 0:
        return None
    if current is None:
        return None
    return round(((current - previous) / previous) * 100, 1)


def get_comparison_periods(year_month: str) -> Dict[str, str]:
    """Get the year_month values for MoM and YoY comparison.
    
    Args:
        year_month: Current period in 'YYYY-MM' format.
        
    Returns:
        Dictionary with 'mom' (previous month) and 'yoy' (same month last year).
    """
    try:
        parts = year_month.split('-')
        if len(parts) != 2:
            raise ValueError
        year = int(parts[0])
        month = int(parts[1])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid format: '{year_month}'. Expected 'YYYY-MM'")

    if not (1 <= month <= 12):
        raise ValueError(f"Invalid month: {month}. Must be between 1 and 12")
    
    # Previous month
    if month == 1:
        mom_year = year - 1
        mom_month = 12
    else:
        mom_year = year
        mom_month = month - 1
    
    # Same month last year
    yoy_year = year - 1
    yoy_month = month
    
    return {
        'mom': f"{mom_year:04d}-{mom_month:02d}",
        'yoy': f"{yoy_year:04d}-{yoy_month:02d}"
    }


def format_change(change: Optional[float]) -> str:
    """Format percentage change for display.
    
    Args:
        change: Percentage change value or None.
        
    Returns:
        Formatted string like '+15%', '-10%', or 'N/A'.
    """
    if change is None:
        return "N/A"
    if change >= 0:
        return f"+{change:.0f}%"
    else:
        return f"{change:.0f}%"


def compute_comparisons(
    current_stats: Dict[str, Any],
    historical_getter: Callable[[str], Optional[Dict[str, Any]]],
    year_month: str,
    metrics: List[str]
) -> Dict[str, Dict[str, Optional[float]]]:
    """Compute MoM and YoY percentage changes for a list of metrics.
    
    Args:
        current_stats: Dictionary of current period's metric values.
        historical_getter: Function that takes a year_month string and returns stats dict.
        year_month: Current period in 'YYYY-MM' format.
        metrics: List of metric keys to compute comparisons for.
        
    Returns:
        Dictionary mapping metric names to their MoM/YoY changes.
        Example: {'articles': {'mom': 15.0, 'yoy': -5.0}, 'reading_time_mins': {'mom': 20.0, 'yoy': None}}
    """
    periods = get_comparison_periods(year_month)
    
    # Fetch historical data
    mom_stats = historical_getter(periods['mom'])
    yoy_stats = historical_getter(periods['yoy'])
    
    result = {}
    for metric in metrics:
        current_value = current_stats.get(metric)
        
        mom_value = mom_stats.get(metric) if mom_stats else None
        yoy_value = yoy_stats.get(metric) if yoy_stats else None
        
        result[metric] = {
            'mom': compute_percentage_change(current_value, mom_value),
            'yoy': compute_percentage_change(current_value, yoy_value)
        }
    
    return result


def format_value_with_changes(
    value: Any,
    changes: Dict[str, Optional[float]],
    value_format: str = "{value}"
) -> str:
    """Format a value with its MoM/YoY changes appended.
    
    Args:
        value: The metric value to display.
        changes: Dictionary with 'mom' and 'yoy' percentage changes.
        value_format: Format string for the value (use {value} placeholder).
        
    Returns:
        Formatted string like "42 (+15% MoM, -5% YoY)".
    """
    formatted_value = value_format.format(value=value)
    mom = format_change(changes.get('mom'))
    yoy = format_change(changes.get('yoy'))
    
    return f"{formatted_value} ({mom} MoM, {yoy} YoY)"


def format_comparison_suffix(changes: Optional[Dict[str, Optional[float]]]) -> str:
    """Format MoM/YoY changes as a suffix string.
    
    Args:
        changes: Dictionary with 'mom' and 'yoy' percentage changes, or None.
        
    Returns:
        Formatted string like ' (+15% MoM, -5% YoY)' or empty if no data.
    """
    if not changes:
        return ""
    
    mom = format_change(changes.get('mom'))
    yoy = format_change(changes.get('yoy'))
    
    return f" ({mom} MoM, {yoy} YoY)"
