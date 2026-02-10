"""Tests for the DataGenerator module."""

import pytest
from src.publish.data_generator import DataGenerator, _to_yaml


class TestToYaml:
    """Tests for the _to_yaml helper function."""
    
    def test_simple_records(self):
        """Test basic YAML output format."""
        records = [
            {'month': '2025-08', 'count': 5},
            {'month': '2025-09', 'count': 10},
        ]
        result = _to_yaml(records, "Test data")
        
        assert result.startswith("# Test data\n")
        assert '- month: "2025-08"' in result
        assert '  count: 5' in result
        assert '- month: "2025-09"' in result
        assert '  count: 10' in result
    
    def test_float_formatting(self):
        """Test that floats are formatted to 2 decimal places."""
        records = [{'month': '2025-08', 'rating': 3.83333}]
        result = _to_yaml(records, "Test")
        
        assert 'rating: 3.83' in result
    
    def test_string_quoting(self):
        """Test that strings are quoted."""
        records = [{'month': '2025-08', 'name': 'hello'}]
        result = _to_yaml(records, "Test")
        
        assert 'month: "2025-08"' in result
        assert 'name: "hello"' in result
    
    def test_empty_records(self):
        """Test with empty records list."""
        result = _to_yaml([], "Empty")
        assert result == "# Empty\n"
    
    def test_matches_reference_format(self):
        """Test that output matches the reference travel.yaml format."""
        records = [
            {'month': '2025-08', 'checkins': 89, 'unique_places': 82},
        ]
        result = _to_yaml(records, "Monthly travel activity data")
        
        expected_lines = [
            '# Monthly travel activity data',
            '- month: "2025-08"',
            '  checkins: 89',
            '  unique_places: 82',
        ]
        for line in expected_lines:
            assert line in result


class TestDataGeneratorReadwise:
    """Tests for Readwise data generation with a real DB."""
    
    def test_avg_reading_speed_computed(self):
        """Test that avg_reading_speed is computed from words / time."""
        records = [
            {'month': '2025-08', 'articles_archived': 18, 'total_words': 42500,
             'time_spent_minutes': 170, 'avg_reading_speed': 250},
        ]
        yaml = _to_yaml(records, "Monthly reading activity data")
        
        assert 'avg_reading_speed: 250' in yaml


class TestDataGeneratorOutput:
    """Tests for the YAML output structure."""
    
    def test_reading_yaml_structure(self):
        """Verify reading.yaml has the expected field names."""
        records = [
            {'month': '2025-08', 'articles_archived': 18, 'total_words': 42500,
             'time_spent_minutes': 170, 'avg_reading_speed': 250},
        ]
        yaml = _to_yaml(records, "Monthly reading activity data")
        
        assert 'articles_archived:' in yaml
        assert 'total_words:' in yaml
        assert 'time_spent_minutes:' in yaml
        assert 'avg_reading_speed:' in yaml
    
    def test_movies_yaml_structure(self):
        """Verify movies.yaml has the expected field names."""
        records = [
            {'month': '2025-08', 'movies_watched': 3, 'avg_rating': 3.83},
        ]
        yaml = _to_yaml(records, "Monthly movies activity data")
        
        assert 'movies_watched:' in yaml
        assert 'avg_rating:' in yaml
    
    def test_podcasts_yaml_structure(self):
        """Verify podcasts.yaml has the expected field names."""
        records = [
            {'month': '2025-08', 'feeds_added': 2, 'feeds_removed': 1, 'episodes_played': 28},
        ]
        yaml = _to_yaml(records, "Monthly podcasts activity data")
        
        assert 'feeds_added:' in yaml
        assert 'feeds_removed:' in yaml
        assert 'episodes_played:' in yaml
    
    def test_travel_yaml_structure(self):
        """Verify travel.yaml has the expected field names."""
        records = [
            {'month': '2025-08', 'checkins': 89, 'unique_places': 82},
        ]
        yaml = _to_yaml(records, "Monthly travel activity data")
        
        assert 'checkins:' in yaml
        assert 'unique_places:' in yaml
    
    def test_records_sorted_ascending(self):
        """Test that records appear in order in the output."""
        records = [
            {'month': '2025-08', 'count': 1},
            {'month': '2025-09', 'count': 2},
            {'month': '2025-10', 'count': 3},
        ]
        yaml = _to_yaml(records, "Test")
        
        pos_08 = yaml.index('2025-08')
        pos_09 = yaml.index('2025-09')
        pos_10 = yaml.index('2025-10')
        
        assert pos_08 < pos_09 < pos_10
