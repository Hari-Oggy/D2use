"""
User-Friendly Error Messages

Provides clear, actionable error messages instead of cryptic stack traces.
Users should know exactly what went wrong and how to fix it.
"""

import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Categorized error codes for better handling"""
    # Authentication
    AUTH_KAGGLE_INVALID = "AUTH001"
    AUTH_HUGGINGFACE_INVALID = "AUTH002"
    AUTH_TOKEN_EXPIRED = "AUTH003"
    
    # Network
    NET_CONNECTION_FAILED = "NET001"
    NET_TIMEOUT = "NET002"
    NET_RATE_LIMITED = "NET003"
    NET_DOWNLOAD_INCOMPLETE = "NET004"
    
    # Data
    DATA_ENCODING_ERROR = "DATA001"
    DATA_PARSE_ERROR = "DATA002"
    DATA_EMPTY_FILE = "DATA003"
    DATA_CORRUPT_FILE = "DATA004"
    DATA_TOO_LARGE = "DATA005"
    DATA_UNSUPPORTED_FORMAT = "DATA006"
    
    # Dataset
    DATASET_NOT_FOUND = "DS001"
    DATASET_ACCESS_DENIED = "DS002"
    DATASET_EMPTY_RESULTS = "DS003"
    
    # System
    SYS_OUT_OF_MEMORY = "SYS001"
    SYS_DISK_FULL = "SYS002"
    SYS_LLM_UNAVAILABLE = "SYS003"


# User-friendly error messages with solutions
ERROR_MESSAGES = {
    # Authentication errors
    ErrorCode.AUTH_KAGGLE_INVALID: {
        "title": "🔑 Kaggle Authentication Failed",
        "message": "Your Kaggle API credentials are invalid or missing.",
        "solution": [
            "1. Go to https://www.kaggle.com/settings/account",
            "2. Click 'Create New API Token' to download kaggle.json",
            "3. Update your .env file with KAGGLE_USERNAME and KAGGLE_KEY",
            "4. Or place kaggle.json in ~/.kaggle/ folder"
        ]
    },
    ErrorCode.AUTH_HUGGINGFACE_INVALID: {
        "title": "🔑 HuggingFace Authentication Failed",
        "message": "Your HuggingFace token is invalid or missing.",
        "solution": [
            "1. Go to https://huggingface.co/settings/tokens",
            "2. Create a new token with 'read' access",
            "3. Add to .env: HF_TOKEN=hf_xxxxx"
        ]
    },
    ErrorCode.AUTH_TOKEN_EXPIRED: {
        "title": "⏰ API Token Expired",
        "message": "Your authentication token has expired.",
        "solution": [
            "1. Generate a new token from the respective platform",
            "2. Update your .env file with the new token",
            "3. Restart the application"
        ]
    },
    
    # Network errors
    ErrorCode.NET_CONNECTION_FAILED: {
        "title": "🌐 Connection Failed",
        "message": "Could not connect to the data source.",
        "solution": [
            "1. Check your internet connection",
            "2. Verify the service is not blocked by firewall",
            "3. Try again in a few minutes"
        ]
    },
    ErrorCode.NET_TIMEOUT: {
        "title": "⏱️ Request Timeout",
        "message": "The download took too long and was cancelled.",
        "solution": [
            "1. Try with a smaller dataset (--max-rows 1000)",
            "2. Check your internet speed",
            "3. The server may be overloaded, try again later"
        ]
    },
    ErrorCode.NET_RATE_LIMITED: {
        "title": "🚦 Rate Limited",
        "message": "Too many requests. The API is throttling you.",
        "solution": [
            "1. Wait 1-2 minutes before trying again",
            "2. Reduce the number of search queries",
            "3. Consider using cached results"
        ]
    },
    ErrorCode.NET_DOWNLOAD_INCOMPLETE: {
        "title": "📥 Download Incomplete",
        "message": "The file download was interrupted.",
        "solution": [
            "1. Check your network stability",
            "2. The file will be re-downloaded automatically",
            "3. If persistent, try a smaller dataset"
        ]
    },
    
    # Data errors
    ErrorCode.DATA_ENCODING_ERROR: {
        "title": "📝 Encoding Error",
        "message": "The file contains characters that couldn't be decoded.",
        "solution": [
            "1. The system will auto-detect encoding",
            "2. If issues persist, try converting file to UTF-8",
            "3. Use a text editor like VS Code to check encoding"
        ]
    },
    ErrorCode.DATA_PARSE_ERROR: {
        "title": "🔍 Parse Error",
        "message": "The data file couldn't be parsed correctly.",
        "solution": [
            "1. Check if the file is corrupted",
            "2. Verify the file format matches the extension",
            "3. Try downloading the file again"
        ]
    },
    ErrorCode.DATA_EMPTY_FILE: {
        "title": "📭 Empty File",
        "message": "The downloaded file is empty.",
        "solution": [
            "1. The dataset may have been removed",
            "2. Try a different dataset",
            "3. Check if you have access to the dataset"
        ]
    },
    ErrorCode.DATA_TOO_LARGE: {
        "title": "📦 File Too Large",
        "message": "The dataset exceeds the maximum allowed size.",
        "solution": [
            "1. Use --max-rows to limit data: --max-rows 5000",
            "2. Increase MAX_FILE_SIZE_MB in .env",
            "3. Consider sampling the data"
        ]
    },
    ErrorCode.DATA_UNSUPPORTED_FORMAT: {
        "title": "📄 Unsupported Format",
        "message": "This file format is not supported.",
        "solution": [
            "1. Supported: CSV, Parquet, JSON, JSONL, Excel (.xlsx/.xls)",
            "2. Convert your file to a supported format",
            "3. Try a different dataset"
        ]
    },
    
    # Dataset errors
    ErrorCode.DATASET_NOT_FOUND: {
        "title": "🔎 Dataset Not Found",
        "message": "No datasets matching your query were found.",
        "solution": [
            "1. Try different keywords",
            "2. Be more specific: 'credit card fraud' instead of 'fraud'",
            "3. Search directly on Kaggle/HuggingFace first"
        ]
    },
    ErrorCode.DATASET_ACCESS_DENIED: {
        "title": "🚫 Access Denied",
        "message": "You don't have permission to access this dataset.",
        "solution": [
            "1. The dataset may require acceptance of terms on Kaggle",
            "2. Visit the dataset page and accept any agreements",
            "3. Try a public dataset instead"
        ]
    },
    
    # System errors
    ErrorCode.SYS_OUT_OF_MEMORY: {
        "title": "💾 Out of Memory",
        "message": "Not enough RAM to process this dataset.",
        "solution": [
            "1. Use --max-rows to limit size: --max-rows 5000",
            "2. Close other applications",
            "3. Process in smaller batches"
        ]
    },
    ErrorCode.SYS_LLM_UNAVAILABLE: {
        "title": "🤖 LM Studio Not Running",
        "message": "Cannot connect to LM Studio for AI-powered cleaning.",
        "solution": [
            "1. Start LM Studio and load a model",
            "2. Click 'Start Server' in Local Server tab",
            "3. Or disable AI: USE_LOCAL_LLM=false in .env"
        ]
    },
}


class UserFriendlyError(Exception):
    """Exception with user-friendly message and solutions"""
    
    def __init__(self, code: ErrorCode, details: Optional[str] = None):
        self.code = code
        self.details = details
        
        error_info = ERROR_MESSAGES.get(code, {})
        self.title = error_info.get("title", "❌ Error")
        self.message = error_info.get("message", "An unexpected error occurred.")
        self.solutions = error_info.get("solution", [])
        
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format error for display"""
        lines = [
            "",
            "=" * 60,
            self.title,
            "=" * 60,
            "",
            f"Problem: {self.message}",
        ]
        
        if self.details:
            lines.append(f"Details: {self.details}")
        
        if self.solutions:
            lines.append("")
            lines.append("💡 How to fix:")
            for solution in self.solutions:
                lines.append(f"   {solution}")
        
        lines.append("")
        lines.append(f"Error Code: {self.code.value}")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def log(self):
        """Log the error with proper formatting"""
        logger.error(self.format_message())


def format_user_error(code: ErrorCode, details: Optional[str] = None) -> str:
    """Format an error for user display without raising exception"""
    error = UserFriendlyError(code, details)
    return error.format_message()


def print_user_error(code: ErrorCode, details: Optional[str] = None):
    """Print a user-friendly error message"""
    print(format_user_error(code, details))


# Test
if __name__ == "__main__":
    print("Testing User-Friendly Error Messages")
    print()
    
    # Test Kaggle auth error
    print_user_error(ErrorCode.AUTH_KAGGLE_INVALID)
    
    # Test with details
    print_user_error(ErrorCode.NET_TIMEOUT, "Download of 'credit_fraud.csv' timed out after 60s")
