from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field

class SourceType(str, Enum):
    HUGGINGFACE = "huggingface"
    KAGGLE = "kaggle"
    WEB_SCRAPE = "web_scrape"

class LicenseInfo(BaseModel):
    """License information for a dataset"""
    license_type: str = Field(..., description="License identifier (e.g., MIT, CC0-1.0)")
    allows_commercial: bool = Field(..., description="Whether commercial use is allowed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in license detection")

class DatasetCandidate(BaseModel):
    """
    Standardized model for a dataset candidate from any source.
    """
    source_id: str = Field(..., description="Unique identifier from the source (e.g., 'username/dataset' or URL)")
    url: HttpUrl = Field(..., description="Direct link to the dataset page")
    source_type: SourceType = Field(..., description="Origin of the dataset")
    is_downloadable: bool = Field(..., description="Whether the dataset can be downloaded directly")
    file_metadata: Dict[str, Any] = Field(..., description="Metadata about the files (must include size_mb, file_extension)")
    compliance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Compliance score from 0.0 to 1.0")
    license_info: Optional[LicenseInfo] = Field(default=None, description="License information if available")

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "stanfordnlp/imdb",
                "url": "https://huggingface.co/datasets/stanfordnlp/imdb",
                "source_type": "huggingface",
                "is_downloadable": True,
                "file_metadata": {"size_mb": 80.5, "file_extension": "parquet"},
                "compliance_score": 0.95,
                "license_info": {
                    "license_type": "MIT",
                    "allows_commercial": True,
                    "confidence": 0.9
                }
            }
        }
