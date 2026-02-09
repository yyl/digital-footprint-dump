"""Tests for the comparison utility module."""

import pytest
from src.comparison import (
    compute_percentage_change,
    get_comparison_periods,
    format_change,
    compute_comparisons,
    format_value_with_changes
)


class TestComputePercentageChange:
    """Tests for compute_percentage_change function."""
    
    def test_increase(self):
        """Test positive percentage change."""
        assert compute_percentage_change(120, 100) == 20.0
    
    def test_decrease(self):
        """Test negative percentage change."""
        assert compute_percentage_change(80, 100) == -20.0
    
    def test_no_change(self):
        """Test zero percentage change."""
        assert compute_percentage_change(100, 100) == 0.0
    
    def test_previous_zero(self):
        """Test when previous value is zero."""
        assert compute_percentage_change(100, 0) is None
    
    def test_previous_none(self):
        """Test when previous value is None."""
        assert compute_percentage_change(100, None) is None
    
    def test_current_none(self):
        """Test when current value is None."""
        assert compute_percentage_change(None, 100) is None
    
    def test_rounding(self):
        """Test that result is rounded to 1 decimal place."""
        # 33.333... should round to 33.3
        assert compute_percentage_change(40, 30) == 33.3


class TestGetComparisonPeriods:
    """Tests for get_comparison_periods function."""
    
    def test_mid_year(self):
        """Test getting periods for a mid-year month."""
        result = get_comparison_periods("2026-06")
        assert result['mom'] == "2026-05"
        assert result['yoy'] == "2025-06"
    
    def test_january(self):
        """Test January wraps to December of previous year for MoM."""
        result = get_comparison_periods("2026-01")
        assert result['mom'] == "2025-12"
        assert result['yoy'] == "2025-01"
    
    def test_december(self):
        """Test December."""
        result = get_comparison_periods("2025-12")
        assert result['mom'] == "2025-11"
        assert result['yoy'] == "2024-12"


class TestFormatChange:
    """Tests for format_change function."""
    
    def test_positive(self):
        """Test positive change formatting."""
        assert format_change(15.0) == "+15%"
    
    def test_negative(self):
        """Test negative change formatting."""
        assert format_change(-10.0) == "-10%"
    
    def test_zero(self):
        """Test zero change formatting."""
        assert format_change(0.0) == "+0%"
    
    def test_none(self):
        """Test None value formatting."""
        assert format_change(None) == "N/A"
    
    def test_rounds_to_integer(self):
        """Test that percentages are formatted as integers."""
        assert format_change(15.7) == "+16%"
        assert format_change(-10.3) == "-10%"


class TestComputeComparisons:
    """Tests for compute_comparisons function."""
    
    def test_with_full_history(self):
        """Test with both MoM and YoY data available."""
        current = {'articles': 120, 'words': 50000}
        
        def getter(period):
            if period == "2026-01":  # MoM
                return {'articles': 100, 'words': 40000}
            elif period == "2025-02":  # YoY
                return {'articles': 80, 'words': 60000}
            return None
        
        result = compute_comparisons(current, getter, "2026-02", ['articles', 'words'])
        
        assert result['articles']['mom'] == 20.0
        assert result['articles']['yoy'] == 50.0
        assert result['words']['mom'] == 25.0
        assert result['words']['yoy'] == pytest.approx(-16.7, abs=0.1)
    
    def test_with_missing_history(self):
        """Test when historical data is not available."""
        current = {'articles': 100}
        
        def getter(period):
            return None
        
        result = compute_comparisons(current, getter, "2026-02", ['articles'])
        
        assert result['articles']['mom'] is None
        assert result['articles']['yoy'] is None


class TestFormatValueWithChanges:
    """Tests for format_value_with_changes function."""
    
    def test_basic_formatting(self):
        """Test basic value with changes formatting."""
        changes = {'mom': 15.0, 'yoy': -5.0}
        result = format_value_with_changes(42, changes)
        assert result == "42 (+15% MoM, -5% YoY)"
    
    def test_with_custom_format(self):
        """Test with custom value format."""
        changes = {'mom': 10.0, 'yoy': None}
        result = format_value_with_changes(1000, changes, value_format="{value:,}")
        assert result == "1,000 (+10% MoM, N/A YoY)"
