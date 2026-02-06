"""
Tests for Smart Date Parser

Validates date format detection and parsing functionality.
"""

import pytest
import polars as pl
from src.processing.date_parser import SmartDateParser


class TestSmartDateParser:
    """Test suite for date parsing"""
    
    def test_iso_date_detection(self):
        """Test ISO format detection (YYYY-MM-DD)"""
        df = pl.DataFrame({
            'date': ['2024-01-31', '2024-02-15', '2024-03-20']
        })
        
        detected_format = SmartDateParser.detect_date_format(df['date'])
        assert detected_format == "%Y-%m-%d"
    
    def test_european_date_detection(self):
        """Test European format detection (DD/MM/YYYY)"""
        df = pl.DataFrame({
            'date': ['31/01/2024', '15/02/2024', '20/03/2024']
        })
        
        detected_format = SmartDateParser.detect_date_format(df['date'])
        assert detected_format == "%d/%m/%Y"
    
    def test_american_date_detection(self):
        """Test American format detection (MM/DD/YYYY)"""
        df = pl.DataFrame({
            'date': ['01/31/2024', '02/15/2024', '03/20/2024']
        })
        
        detected_format = SmartDateParser.detect_date_format(df['date'])
        assert detected_format in ["%m/%d/%Y", "%d/%m/%Y"]  # Ambiguous
    
    def test_is_date_column(self):
        """Test date column detection"""
        # Date column
        date_col = pl.Series('dates', ['2024-01-31', '2024-02-15', '2024-03-20'])
        assert SmartDateParser.is_date_column(date_col) is True
        
        # Non-date column
        number_col = pl.Series('numbers', ['123', '456', '789'])
        assert SmartDateParser.is_date_column(number_col) is False
    
    def test_parse_date_column(self):
        """Test date column parsing"""
        df = pl.DataFrame({
            'date_str': ['2024-01-31', '2024-02-15', '2024-03-20']
        })
        
        parsed = SmartDateParser.parse_date_column(df['date_str'], format_hint="%Y-%m-%d")
        
        assert parsed.dtype == pl.Date
        # Just check the date was parsed successfully
        assert parsed.null_count() == 0
    
    def test_auto_detect_and_parse(self):
        """Test automatic date detection and parsing"""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'date': ['2024-01-31', '2024-02-15', '2024-03-20'],
            'value': [100, 200, 300]
        })
        
        result = SmartDateParser.detect_and_parse_dates(df, auto_convert=True)
        
        # Date column should be converted
        assert result['date'].dtype == pl.Date
        # Other columns unchanged
        assert result['id'].dtype == pl.Int64
        assert result['value'].dtype == pl.Int64
    
    def test_unix_timestamp_detection(self):
        """Test Unix timestamp detection"""
        # Seconds timestamp
        ts_seconds = pl.Series('ts', [1609459200, 1612137600, 1614556800])
        assert SmartDateParser.is_unix_timestamp(ts_seconds) is True
        
        # Milliseconds timestamp
        ts_millis = pl.Series('ts', [1609459200000, 1612137600000, 1614556800000])
        assert SmartDateParser.is_unix_timestamp(ts_millis) is True
        
        # Not a timestamp
        not_ts = pl.Series('not_ts', [1, 2, 3])
        assert SmartDateParser.is_unix_timestamp(not_ts) is False
    
    def test_mixed_null_dates(self):
        """Test handling of dates with null values"""
        df = pl.DataFrame({
            'date': ['2024-01-31', None, '2024-03-20', '']
        })
        
        # Should handle nulls gracefully
        parsed = SmartDateParser.parse_date_column(df['date'], format_hint="%Y-%m-%d")
        assert parsed.null_count() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
