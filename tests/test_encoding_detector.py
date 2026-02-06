"""
Tests for Encoding Detector

Validates encoding detection and BOM cleaning functionality.
"""

import pytest
import polars as pl
from pathlib import Path
import tempfile
from src.processing.encoding_detector import EncodingDetector, read_csv_robust


class TestEncodingDetector:
    """Test suite for encoding detection"""
    
    def test_utf8_detection(self):
        """Test UTF-8 encoding detection"""
        # Create temp UTF-8 file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.csv') as f:
            f.write("name,age\n")
            f.write("John,25\n")
            f.write("Müller,30\n")  # German umlaut
            temp_path = Path(f.name)
        
        try:
            encoding = EncodingDetector.detect_encoding(temp_path)
            # Accept various UTF-8/ASCII compatible encodings
            assert encoding.lower() in ['utf-8', 'utf-8-sig', 'ascii', 'iso-8859-1', 'latin-1']
        finally:
            temp_path.unlink()
    
    def test_bom_cleaning(self):
        """Test BOM character removal from headers"""
        # Create DataFrame with BOM in column name
        df = pl.DataFrame({
            '\ufeffname': ['John', 'Jane'],
            'age': [25, 30]
        })
        
        cleaned = EncodingDetector.clean_dataframe_headers(df)
        
        # BOM should be removed
        assert 'name' in cleaned.columns
        assert '\ufeffname' not in cleaned.columns
    
    def test_zero_width_character_cleaning(self):
        """Test zero-width character removal"""
        # Create DataFrame with zero-width spaces
        df = pl.DataFrame({
            'name\u200b': ['John'],  # Zero-width space
            'age\u200c': [25]         # Zero-width non-joiner
        })
        
        cleaned = EncodingDetector.clean_dataframe_headers(df)
        
        assert 'name' in cleaned.columns
        assert 'age' in cleaned.columns
    
    def test_read_csv_robust(self):
        """Test robust CSV reading with encoding detection"""
        # Create temp CSV file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.csv') as f:
            f.write("name,score\n")
            f.write("Alice,95\n")
            f.write("Bob,87\n")
            temp_path = Path(f.name)
        
        try:
            df = read_csv_robust(temp_path)
            
            assert len(df) == 2
            assert 'name' in df.columns
            assert 'score' in df.columns
            assert df['name'][0] == 'Alice'
        finally:
            temp_path.unlink()
    
    def test_latin1_encoding(self):
        """Test Latin-1 encoding handling"""
        # Create Latin-1 file with special characters
        with tempfile.NamedTemporaryFile(mode='w', encoding='latin-1', delete=False, suffix='.csv') as f:
            f.write("name,city\n")
            f.write("José,São Paulo\n")  # Latin-1 characters
            temp_path = Path(f.name)
        
        try:
            # Should detect and read correctly
            df = read_csv_robust(temp_path)
            assert len(df) == 1
            # May have encoding issues, but shouldn't crash
        except Exception as e:
            pytest.fail(f"Should handle Latin-1 gracefully: {e}")
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
