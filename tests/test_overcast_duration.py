import pytest
from src.overcast.duration import parse_duration

def test_parse_duration_seconds():
    assert parse_duration("1541") == 1541
    assert parse_duration("3726") == 3726
    assert parse_duration("0") == 0

def test_parse_duration_mm_ss():
    assert parse_duration("24:09") == 1449
    assert parse_duration("01:00") == 60
    assert parse_duration("0:00") == 0

def test_parse_duration_hh_mm_ss():
    assert parse_duration("02:31:53") == 9113
    assert parse_duration("00:46:06") == 2766
    assert parse_duration("1:00:00") == 3600

def test_parse_duration_invalid():
    assert parse_duration(None) is None
    assert parse_duration("") is None
    assert parse_duration("  ") is None
    
    with pytest.raises(ValueError, match="Unknown duration format"):
        parse_duration("invalid")
    
    with pytest.raises(ValueError, match="Invalid MM:SS duration format"):
        parse_duration("12:invalid")
        
    with pytest.raises(ValueError, match="Unknown duration format"):
        parse_duration("12:34:56:78")
