import asyncio
import json
import os
from typing import List
from pathlib import Path
from pydantic import HttpUrl
import logging

from ..schemas import DatasetCandidate, SourceType
from ..config import settings
from src.utils.retry import retry_api_call

logger = logging.getLogger(__name__)

class KaggleAdapter:
    """
    Adapter for searching datasets on Kaggle.
    """
    
    def __init__(self):
        self._setup_credentials()
    
    def _setup_credentials(self):
        """
        Set up Kaggle credentials from environment variables.
        Kaggle API expects credentials in ~/.kaggle/kaggle.json
        """
        kaggle_dir = Path.home() / ".kaggle"
        kaggle_dir.mkdir(exist_ok=True)
        
        kaggle_json = kaggle_dir / "kaggle.json"
        
        credentials = {
            "username": settings.KAGGLE_USERNAME,
            "key": settings.KAGGLE_KEY
        }
        
        with open(kaggle_json, "w") as f:
            json.dump(credentials, f)
        
        # Set permissions (Kaggle requires 600)
        os.chmod(kaggle_json, 0o600)
        
        logger.info("Kaggle credentials configured")
    
    @retry_api_call
    async def search_datasets(self, query: str, limit: int = 10) -> List[DatasetCandidate]:
        """
        Search for datasets on Kaggle.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of standardized DatasetCandidate objects
        """
        try:
            logger.info(f"Searching Kaggle for: {query}")
            
            # Import here to avoid issues if kaggle not installed
            from kaggle.api.kaggle_api_extended import KaggleApi
            
            # Initialize and authenticate
            api = KaggleApi()
            api.authenticate()
            
            # Run blocking Kaggle API call in thread pool
            loop = asyncio.get_event_loop()
            datasets = await loop.run_in_executor(
                None,
                lambda: api.dataset_list(search=query, page=1)
            )
            
            # Limit results manually since API doesn't have page_size
            datasets = datasets[:limit]
            
            candidates = []
            for dataset in datasets:
                try:
                    # Extract metadata
                    dataset_id = dataset.ref  # Format: "username/dataset-name"
                    url = f"https://www.kaggle.com/datasets/{dataset_id}"
                    
                    # Get file size (Kaggle provides in bytes)
                    # Use getattr with default to handle missing attributes
                    total_bytes = getattr(dataset, 'totalBytes', 0) or getattr(dataset, 'total_bytes', 0) or 0
                    size_mb = total_bytes / (1024 * 1024) if total_bytes else 0.0
                    
                    # Kaggle datasets are typically CSV or ZIP
                    file_extension = "csv"  # Default assumption
                    
                    # Get download and vote counts safely
                    downloads = getattr(dataset, 'downloadCount', 0) or getattr(dataset, 'download_count', 0) or 0
                    votes = getattr(dataset, 'voteCount', 0) or getattr(dataset, 'vote_count', 0) or 0
                    usability = getattr(dataset, 'usabilityRating', 0.0) or getattr(dataset, 'usability_rating', 0.0) or 0.0
                    
                    candidate = DatasetCandidate(
                        source_id=dataset_id,
                        url=HttpUrl(url),
                        source_type=SourceType.KAGGLE,
                        is_downloadable=True,  # Kaggle datasets are downloadable
                        file_metadata={
                            "size_mb": size_mb,
                            "file_extension": file_extension,
                            "downloads": downloads,
                            "votes": votes,
                            "usability": usability
                        },
                        compliance_score=0.0  # Will be calculated later
                    )
                    candidates.append(candidate)
                    
                except Exception as e:
                    logger.warning(f"Failed to process Kaggle dataset {getattr(dataset, 'ref', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Found {len(candidates)} datasets on Kaggle")
            return candidates
            
        except Exception as e:
            logger.error(f"Kaggle search failed: {e}")
            return []


# Test function for manual verification
async def test_kaggle_adapter():
    """Test the Kaggle adapter"""
    adapter = KaggleAdapter()
    results = await adapter.search_datasets("cancer", limit=5)
    
    print(f"\n{'='*60}")
    print(f"Kaggle Search Results: 'cancer'")
    print(f"{'='*60}\n")
    
    for i, dataset in enumerate(results, 1):
        print(f"{i}. {dataset.source_id}")
        print(f"   URL: {dataset.url}")
        print(f"   Downloads: {dataset.file_metadata.get('downloads', 0)}")
        print(f"   Votes: {dataset.file_metadata.get('votes', 0)}")
        print(f"   Size: {dataset.file_metadata.get('size_mb', 0):.2f} MB")
        print()


if __name__ == "__main__":
    asyncio.run(test_kaggle_adapter())
