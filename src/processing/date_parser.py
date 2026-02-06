"""
Smart Date Parser

Automatically detects and parses dates in multiple formats.
Handles European (DD/MM/YYYY), American (MM/DD/YYYY), ISO, Excel serial dates, etc.
"""

import logging
from typing import Optional, List
import polars as pl
from datetime import datetime

logger = logging.getLogger(__name__)


class SmartDateParser:
    """
    Parse dates in multiple formats automatically.
    
    Handles:
    - ISO: 2024-01-31
    - European: 31/01/2024, 31-01-2024
    - American: 01/31/2024, 01-31-2024
    - Excel: 31-Jan-2024, Jan 31 2024
    - Compact: 20240131
    - Unix timestamps
    """
    
    DATE_FORMATS = [
        # ISO formats (most common)
        "%Y-%m-%d",           # 2024-01-31
        "%Y/%m/%d",           # 2024/01/31
        "%Y%m%d",             # 20240131
        
        # European formats (DD/MM/YYYY)
        "%d/%m/%Y",           # 31/01/2024
        "%d-%m-%Y",           # 31-01-2024
        "%d.%m.%Y",           # 31.01.2024
        
        # American formats (MM/DD/YYYY)
        "%m/%d/%Y",           # 01/31/2024
        "%m-%d-%Y",           # 01-31-2024
        "%m.%d.%Y",           # 01.31.2024
        
        # Excel-style formats
        "%d-%b-%Y",           # 31-Jan-2024
        "%b %d %Y",           # Jan 31 2024
        "%b %d, %Y",          # Jan 31, 2024
        "%d %b %Y",           # 31 Jan 2024
        
        # With time
        "%Y-%m-%d %H:%M:%S",  # 2024-01-31 10:30:00
        "%d/%m/%Y %H:%M",     # 31/01/2024 10:30
        "%m/%d/%Y %H:%M",     # 01/31/2024 10:30
    ]
    
    @staticmethod
    def detect_date_format(column: pl.Series, sample_size: int = 100) -> Optional[str]:
        """
        Detect which date format a column uses.
        
        Args:
            column: Polars Series (assumed to be string type)
            sample_size: Number of rows to sample for detection
            
        Returns:
            Format string (e.g., "%Y-%m-%d") or None if not a date column
        """
        if column.dtype != pl.Utf8:
            return None
        
        # Sample non-null values
        sample = column.drop_nulls().head(sample_size)
        
        if len(sample) == 0:
            return None
        
        # Try each format
        for fmt in SmartDateParser.DATE_FORMATS:
            try:
                # Try parsing with this format
                parsed = sample.str.strptime(pl.Date, fmt, strict=False)
                
                # Count successful parses
                success_count = len(sample) - parsed.null_count()
                success_rate = success_count / len(sample)
                
                # If >90% success, this is likely the format
                if success_rate > 0.9:
                    logger.info(f"Detected date format: {fmt} (success rate: {success_rate:.0%})")
                    return fmt
                    
            except Exception:
                continue
        
        return None
    
    @staticmethod
    def is_date_column(column: pl.Series, threshold: float = 0.7) -> bool:
        """
        Heuristic: Is this column a date?
        
        Args:
            column: Polars Series
            threshold: Minimum percentage of values that look like dates
            
        Returns:
            True if column appears to be dates
        """
        # Already a date type
        if column.dtype in [pl.Date, pl.Datetime]:
            return True
        
        # Not a string
        if column.dtype != pl.Utf8:
            return False
        
        # Check if format detected
        fmt = SmartDateParser.detect_date_format(column)
        return fmt is not None
    
    @staticmethod
    def parse_date_column(column: pl.Series, format_hint: Optional[str] = None) -> pl.Series:
        """
        Parse a date column to Polars Date type.
        
        Args:
            column: String column containing dates
            format_hint: Optional format string if known
            
        Returns:
            Parsed column as Date type
        """
        if column.dtype in [pl.Date, pl.Datetime]:
            return column  # Already parsed
        
        # Detect format if not provided
        if format_hint is None:
            format_hint = SmartDateParser.detect_date_format(column)
        
        if format_hint is None:
            logger.warning(f"Could not detect date format for column")
            return column  # Return unchanged
        
        try:
            parsed = column.str.strptime(pl.Date, format_hint, strict=False)
            logger.info(f"✅ Parsed date column with format: {format_hint}")
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse dates: {e}")
            return column
    
    @staticmethod
    def detect_and_parse_dates(df: pl.DataFrame, auto_convert: bool = True) -> pl.DataFrame:
        """
        Automatically detect and parse all date columns in a DataFrame.
        
        Args:
            df: Polars DataFrame
            auto_convert: If True, automatically convert detected date columns
            
        Returns:
            DataFrame with date columns converted to Date type
        """
        date_columns = []
        
        for col in df.columns:
            if SmartDateParser.is_date_column(df[col]):
                date_columns.append(col)
                logger.info(f"Detected date column: '{col}'")
        
        if not auto_convert or not date_columns:
            return df
        
        # Convert each date column
        for col in date_columns:
            try:
                df = df.with_columns(
                    SmartDateParser.parse_date_column(df[col]).alias(col)
                )
            except Exception as e:
                logger.warning(f"Could not convert '{col}' to date: {e}")
        
        return df
    
    @staticmethod
    def is_unix_timestamp(column: pl.Series) -> bool:
        """
        Check if column contains Unix timestamps.
        
        Unix timestamps are typically:
        - Integers (10 digits for seconds, 13 for milliseconds)
        - In range 946684800 (2000-01-01) to 2147483647 (2038-01-19)
        """
        if column.dtype not in [pl.Int64, pl.Int32, pl.Float64]:
            return False
        
        sample = column.drop_nulls().head(100)
        if len(sample) == 0:
            return False
        
        # Check if values are in Unix timestamp range
        min_val = sample.min()
        max_val = sample.max()
        
        # Seconds timestamp range (2000-2040)
        if 946684800 <= min_val and max_val <= 2524608000:
            return True
        
        # Milliseconds timestamp range  
        if 946684800000 <= min_val and max_val <= 2524608000000:
            return True
        
        return False
    
    @staticmethod
    def parse_unix_timestamp(column: pl.Series) -> pl.Series:
        """
        Parse Unix timestamps to Date.
        
        Handles both seconds and milliseconds timestamps.
        """
        sample = column.drop_nulls().head(1)
        if len(sample) == 0:
            return column
        
        first_val = sample[0]
        
        # Milliseconds timestamp (13 digits)
        if first_val > 9999999999:
            return pl.from_epoch(column, time_unit="ms").cast(pl.Date)
        else:
            # Seconds timestamp (10 digits)
            return pl.from_epoch(column, time_unit="s").cast(pl.Date)


def auto_detect_and_parse_dates(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convenience function to automatically detect and parse all date columns.
    
    This is the recommended way to handle date columns.
    
    Args:
        df: Polars DataFrame
        
    Returns:
        DataFrame with date columns converted
    """
    return SmartDateParser.detect_and_parse_dates(df, auto_convert=True)
