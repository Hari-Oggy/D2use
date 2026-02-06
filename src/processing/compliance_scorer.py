from typing import Dict
import logging

from ..schemas import DatasetCandidate
from .license_detector import LicenseDetector

logger = logging.getLogger(__name__)

class ComplianceScorer:
    """
    Calculates compliance score for datasets based on:
    - License availability and type
    - Downloadability
    - Metadata completeness
    - File format
    """
    
    def __init__(self):
        self.license_detector = LicenseDetector()
    
    def calculate_score(self, dataset: DatasetCandidate, metadata: Dict = None) -> float:
        """
        Calculate compliance score (0.0 to 1.0).
        
        Args:
            dataset: DatasetCandidate object
            metadata: Optional extracted metadata from scraping
            
        Returns:
            Compliance score between 0.0 and 1.0
        """
        score = 0.0
        max_score = 1.0
        
        # 1. License Score (0.4 points)
        license_score = self._score_license(dataset, metadata)
        score += license_score * 0.4
        
        # 2. Downloadability (0.3 points)
        if dataset.is_downloadable:
            score += 0.3
        
        # 3. Metadata Completeness (0.2 points)
        metadata_score = self._score_metadata(dataset, metadata)
        score += metadata_score * 0.2
        
        # 4. File Format (0.1 points)
        format_score = self._score_format(dataset)
        score += format_score * 0.1
        
        logger.info(f"Compliance score for {dataset.source_id}: {score:.2f}")
        return round(score, 2)
    
    def _score_license(self, dataset: DatasetCandidate, metadata: Dict = None) -> float:
        """Score based on license (0.0 to 1.0)"""
        # Check metadata first
        license_id = None
        if metadata and metadata.get("license"):
            license_id = metadata["license"]
        
        # Fallback to dataset metadata
        if not license_id and dataset.file_metadata.get("license"):
            license_id = dataset.file_metadata["license"]
        
        if not license_id or license_id == "UNKNOWN":
            return 0.0
        
        # Score based on ML-friendliness
        if self.license_detector.is_ml_friendly(license_id):
            return 1.0  # Perfect score for ML-friendly licenses
        
        # Partial score for other recognized licenses
        return 0.5
    
    def _score_metadata(self, dataset: DatasetCandidate, metadata: Dict = None) -> float:
        """Score based on metadata completeness (0.0 to 1.0)"""
        score = 0.0
        
        # Check dataset metadata
        if dataset.file_metadata:
            if dataset.file_metadata.get("size_mb", 0) > 0:
                score += 0.25
            if dataset.file_metadata.get("file_extension") != "unknown":
                score += 0.25
        
        # Check extracted metadata
        if metadata:
            if metadata.get("dataset_name"):
                score += 0.25
            if metadata.get("description"):
                score += 0.25
        
        return min(score, 1.0)
    
    def _score_format(self, dataset: DatasetCandidate) -> float:
        """Score based on file format (0.0 to 1.0)"""
        file_ext = dataset.file_metadata.get("file_extension", "unknown").lower()
        
        # ML-friendly formats
        ml_formats = ["csv", "parquet", "json", "jsonl", "arrow"]
        if file_ext in ml_formats:
            return 1.0
        
        # Acceptable formats
        acceptable_formats = ["xlsx", "tsv", "txt"]
        if file_ext in acceptable_formats:
            return 0.7
        
        # Archive formats (need extraction)
        archive_formats = ["zip", "tar", "gz"]
        if file_ext in archive_formats:
            return 0.5
        
        return 0.0
    
    def get_score_breakdown(self, dataset: DatasetCandidate, metadata: Dict = None) -> Dict:
        """
        Get detailed breakdown of compliance score.
        
        Returns:
            Dict with score components
        """
        license_score = self._score_license(dataset, metadata)
        metadata_score = self._score_metadata(dataset, metadata)
        format_score = self._score_format(dataset)
        
        total_score = (
            license_score * 0.4 +
            (0.3 if dataset.is_downloadable else 0.0) +
            metadata_score * 0.2 +
            format_score * 0.1
        )
        
        return {
            "total_score": round(total_score, 2),
            "components": {
                "license": round(license_score * 0.4, 2),
                "downloadable": 0.3 if dataset.is_downloadable else 0.0,
                "metadata": round(metadata_score * 0.2, 2),
                "format": round(format_score * 0.1, 2)
            },
            "raw_scores": {
                "license": license_score,
                "metadata": metadata_score,
                "format": format_score
            }
        }


# Test function
def test_compliance_scorer():
    """Test compliance scoring with sample datasets"""
    from pydantic import HttpUrl
    from ..schemas import SourceType
    
    scorer = ComplianceScorer()
    
    # Test case 1: Perfect dataset
    perfect_dataset = DatasetCandidate(
        source_id="perfect/dataset",
        url=HttpUrl("https://example.com/perfect"),
        source_type=SourceType.WEB_SCRAPE,
        is_downloadable=True,
        file_metadata={
            "size_mb": 10.5,
            "file_extension": "csv",
            "license": "CC0-1.0"
        },
        compliance_score=0.0
    )
    
    perfect_metadata = {
        "dataset_name": "Perfect Dataset",
        "description": "A well-documented dataset",
        "license": "CC0-1.0"
    }
    
    # Test case 2: Poor dataset
    poor_dataset = DatasetCandidate(
        source_id="poor/dataset",
        url=HttpUrl("https://example.com/poor"),
        source_type=SourceType.WEB_SCRAPE,
        is_downloadable=False,
        file_metadata={
            "size_mb": 0,
            "file_extension": "unknown"
        },
        compliance_score=0.0
    )
    
    print(f"\n{'='*60}")
    print("Compliance Scorer Test")
    print(f"{'='*60}\n")
    
    # Test perfect dataset
    print("Test 1: Perfect Dataset")
    score1 = scorer.calculate_score(perfect_dataset, perfect_metadata)
    breakdown1 = scorer.get_score_breakdown(perfect_dataset, perfect_metadata)
    print(f"Total Score: {score1}")
    print(f"Breakdown: {breakdown1['components']}")
    print()
    
    # Test poor dataset
    print("Test 2: Poor Dataset")
    score2 = scorer.calculate_score(poor_dataset)
    breakdown2 = scorer.get_score_breakdown(poor_dataset)
    print(f"Total Score: {score2}")
    print(f"Breakdown: {breakdown2['components']}")
    print()
    
    print(f"{'='*60}")
    if score1 > 0.8 and score2 < 0.3:
        print("✅ Compliance scorer working correctly!")
    else:
        print("❌ Compliance scorer needs adjustment")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    test_compliance_scorer()
