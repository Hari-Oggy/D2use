import asyncio
from typing import List, Optional
from huggingface_hub import HfApi, list_datasets
from pydantic import HttpUrl
import logging

from ..schemas import DatasetCandidate, SourceType
from ..config import settings
from src.utils.retry import retry_api_call

logger = logging.getLogger(__name__)

class HuggingFaceAdapter:
    """
    Adapter for searching datasets on Hugging Face Hub.
    """
    
    def __init__(self):
        self.api = HfApi(token=settings.HF_TOKEN)
    
    @retry_api_call
    async def search_datasets(self, query: str, limit: int = 10) -> List[DatasetCandidate]:
        """
        Search for datasets on Hugging Face Hub.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of standardized DatasetCandidate objects
        """
        try:
            logger.info(f"Searching Hugging Face for: {query}")
            
            # Run blocking HF API call in thread pool
            loop = asyncio.get_event_loop()
            datasets = await loop.run_in_executor(
                None,
                lambda: list(list_datasets(search=query, limit=limit))
            )
            
            candidates = []
            for dataset in datasets:
                try:
                    # Extract metadata
                    dataset_id = dataset.id
                    url = f"https://huggingface.co/datasets/{dataset_id}"
                    
                    # Get file size if available
                    size_mb = 0.0
                    file_extension = "unknown"
                    
                    # Check if dataset info is available
                    if hasattr(dataset, 'cardData') and dataset.cardData:
                        # Try to get size from card data
                        if hasattr(dataset.cardData, 'dataset_info'):
                            info = dataset.cardData.dataset_info
                            if hasattr(info, 'dataset_size'):
                                size_mb = info.dataset_size / (1024 * 1024)  # Convert to MB
                    
                    # Determine file extension (HF typically uses parquet)
                    file_extension = "parquet"
                    
                    candidate = DatasetCandidate(
                        source_id=dataset_id,
                        url=HttpUrl(url),
                        source_type=SourceType.HUGGINGFACE,
                        is_downloadable=True,  # HF datasets are always downloadable
                        file_metadata={
                            "size_mb": size_mb,
                            "file_extension": file_extension,
                            "downloads": getattr(dataset, 'downloads', 0),
                            "likes": getattr(dataset, 'likes', 0)
                        },
                        compliance_score=0.0  # Will be calculated later
                    )
                    candidates.append(candidate)
                    
                except Exception as e:
                    logger.warning(f"Failed to process HF dataset {dataset.id}: {e}")
                    continue
            
            logger.info(f"Found {len(candidates)} datasets on Hugging Face")
            return candidates
            
        except Exception as e:
            logger.error(f"Hugging Face search failed: {e}")
            return []


# Test function for manual verification
async def test_hf_adapter():
    """Test the Hugging Face adapter"""
    adapter = HuggingFaceAdapter()
    results = await adapter.search_datasets("cancer", limit=5)
    
    print(f"\n{'='*60}")
    print(f"Hugging Face Search Results: 'cancer'")
    print(f"{'='*60}\n")
    
    for i, dataset in enumerate(results, 1):
        print(f"{i}. {dataset.source_id}")
        print(f"   URL: {dataset.url}")
        print(f"   Downloads: {dataset.file_metadata.get('downloads', 0)}")
        print(f"   Size: {dataset.file_metadata.get('size_mb', 0):.2f} MB")
        print()


if __name__ == "__main__":
    asyncio.run(test_hf_adapter())
