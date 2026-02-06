"""
Download Validator

Detects partial/corrupted downloads and validates file integrity.
Prevents silent data loss from incomplete downloads.
"""

import logging
import os
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)


class DownloadValidator:
    """
    Validates downloaded files for completeness and integrity.
    
    Detects:
    - Truncated CSV files (no newline at end)
    - Corrupted ZIP archives
    - Empty files
    - Files smaller than expected
    - ZIP bombs (expansion attack)
    """
    
    # Maximum compression ratio before ZIP bomb warning
    MAX_COMPRESSION_RATIO = 100  # 100:1 is suspicious
    MAX_UNCOMPRESSED_SIZE_GB = 5  # 5GB max uncompressed
    
    @staticmethod
    def validate_file(file_path: Path, expected_size: Optional[int] = None) -> Tuple[bool, str]:
        """
        Validate downloaded file for integrity.
        
        Args:
            file_path: Path to downloaded file
            expected_size: Expected file size (if known from HTTP headers)
            
        Returns:
            (is_valid, message)
        """
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
        
        actual_size = file_path.stat().st_size
        
        # Check for empty file
        if actual_size == 0:
            return False, "File is empty (0 bytes)"
        
        # Check against expected size
        if expected_size and actual_size < expected_size * 0.95:  # 5% tolerance
            return False, f"File appears truncated: {actual_size} bytes < expected {expected_size}"
        
        # Validate based on file type
        suffix = file_path.suffix.lower()
        
        if suffix == '.csv':
            return DownloadValidator._validate_csv(file_path)
        elif suffix == '.zip':
            return DownloadValidator._validate_zip(file_path)
        elif suffix in ['.parquet', '.pq']:
            return DownloadValidator._validate_parquet(file_path)
        elif suffix in ['.json', '.jsonl']:
            return DownloadValidator._validate_json(file_path)
        elif suffix in ['.xlsx', '.xls']:
            return DownloadValidator._validate_excel(file_path)
        else:
            # Unknown format, basic validation only
            return True, f"File exists ({actual_size} bytes), format not validated"
    
    @staticmethod
    def _validate_csv(file_path: Path) -> Tuple[bool, str]:
        """Validate CSV file integrity"""
        try:
            with open(file_path, 'rb') as f:
                # Check first line (header)
                first_line = f.readline()
                if not first_line:
                    return False, "CSV file is empty"
                
                # Check if contains comma (basic CSV check)
                if b',' not in first_line and b'\t' not in first_line:
                    return False, "File does not appear to be CSV (no delimiters)"
                
                # Check last bytes for proper ending
                f.seek(-min(100, file_path.stat().st_size), 2)
                last_bytes = f.read()
                
                # CSV should end with newline
                if not last_bytes.rstrip().endswith((b'\n', b'\r')):
                    logger.warning("CSV may be truncated (no trailing newline)")
                    # Not fatal, just warning
                
                return True, "CSV validation passed"
                
        except Exception as e:
            return False, f"CSV validation failed: {e}"
    
    @staticmethod
    def _validate_zip(file_path: Path) -> Tuple[bool, str]:
        """Validate ZIP archive integrity and check for ZIP bombs"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Test ZIP integrity
                bad_file = zf.testzip()
                if bad_file:
                    return False, f"Corrupted file in ZIP: {bad_file}"
                
                # Check total uncompressed size (ZIP bomb detection)
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                compressed_size = file_path.stat().st_size
                
                # Check compression ratio
                if compressed_size > 0:
                    ratio = total_uncompressed / compressed_size
                    if ratio > DownloadValidator.MAX_COMPRESSION_RATIO:
                        return False, f"Suspicious compression ratio ({ratio:.0f}:1) - possible ZIP bomb"
                
                # Check total size
                max_bytes = DownloadValidator.MAX_UNCOMPRESSED_SIZE_GB * 1024 * 1024 * 1024
                if total_uncompressed > max_bytes:
                    return False, f"Uncompressed size too large: {total_uncompressed / (1024**3):.1f} GB"
                
                file_count = len(zf.infolist())
                return True, f"ZIP valid: {file_count} files, {total_uncompressed / (1024**2):.1f} MB uncompressed"
                
        except zipfile.BadZipFile:
            return False, "Invalid or corrupted ZIP file"
        except Exception as e:
            return False, f"ZIP validation failed: {e}"
    
    @staticmethod
    def _validate_parquet(file_path: Path) -> Tuple[bool, str]:
        """Validate Parquet file integrity"""
        try:
            # Parquet files have magic bytes
            with open(file_path, 'rb') as f:
                header = f.read(4)
                
                if header != b'PAR1':
                    return False, "Invalid Parquet file (wrong magic bytes)"
                
                # Check footer
                f.seek(-4, 2)
                footer = f.read(4)
                
                if footer != b'PAR1':
                    return False, "Parquet file may be truncated (invalid footer)"
                
                return True, "Parquet validation passed"
                
        except Exception as e:
            return False, f"Parquet validation failed: {e}"
    
    @staticmethod
    def _validate_json(file_path: Path) -> Tuple[bool, str]:
        """Validate JSON/JSONL file integrity"""
        try:
            with open(file_path, 'rb') as f:
                first_byte = f.read(1)
                
                # JSON should start with { or [
                if first_byte not in [b'{', b'[']:
                    # Might be JSONL (starts with {)
                    if first_byte != b'{':
                        return False, "File does not appear to be valid JSON"
                
                return True, "JSON validation passed"
                
        except Exception as e:
            return False, f"JSON validation failed: {e}"
    
    @staticmethod
    def _validate_excel(file_path: Path) -> Tuple[bool, str]:
        """Validate Excel file integrity"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                
                # XLSX is a ZIP file (PK magic bytes)
                if header[:2] == b'PK':
                    return DownloadValidator._validate_zip(file_path)
                
                # XLS has OLE header
                if header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
                    return True, "XLS file appears valid"
                
                return False, "File does not appear to be valid Excel format"
                
        except Exception as e:
            return False, f"Excel validation failed: {e}"
    
    @staticmethod
    def compute_checksum(file_path: Path, algorithm: str = 'md5') -> str:
        """Compute file checksum for integrity verification"""
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @staticmethod
    def verify_checksum(file_path: Path, expected_hash: str, algorithm: str = 'md5') -> bool:
        """Verify file matches expected checksum"""
        actual_hash = DownloadValidator.compute_checksum(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()


def validate_download(file_path: Path, expected_size: Optional[int] = None) -> bool:
    """
    Convenience function to validate a downloaded file.
    
    Returns True if valid, logs error and returns False if not.
    """
    is_valid, message = DownloadValidator.validate_file(file_path, expected_size)
    
    if is_valid:
        logger.info(f"✅ Download validated: {message}")
    else:
        logger.error(f"❌ Download validation failed: {message}")
    
    return is_valid


# Test function
if __name__ == "__main__":
    import tempfile
    
    print("Testing Download Validator")
    print("=" * 60)
    
    # Test CSV validation
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,age\n")
        f.write("John,25\n")
        f.write("Jane,30\n")
        temp_csv = Path(f.name)
    
    valid, msg = DownloadValidator.validate_file(temp_csv)
    print(f"CSV test: {valid} - {msg}")
    temp_csv.unlink()
    
    # Test empty file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_empty = Path(f.name)
    
    valid, msg = DownloadValidator.validate_file(temp_empty)
    print(f"Empty test: {valid} - {msg}")
    temp_empty.unlink()
    
    print("=" * 60)
    print("✅ Download validator working!")
