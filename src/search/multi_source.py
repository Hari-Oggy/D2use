"""
Multi-Source Search Orchestrator

Searches across ALL sources: HuggingFace → Kaggle → Web

PROBLEM: Only HuggingFace works, Kaggle/web not integrated
SOLUTION: Try all sources, combine results
"""

import asyncio
import logging
from typing import List

from ..schemas import DatasetCandidate
from ..adapters.huggingface import HuggingFaceAdapter
from ..adapters.kaggle import KaggleAdapter
from ..search.search_bridge import SearchBridge

logger = logging.getLogger(__name__)

class MultiSourceSearch:
    """
    Search across multiple sources and combine results.
    
    Priority:
    1. HuggingFace (fastest, most reliable)
    2. Kaggle (requires API key)
    3. Web scraping (slowest, fallback)
    """
    
    def __init__(self):
        self.hf = HuggingFaceAdapter()
        self.kaggle = KaggleAdapter()
        self.web = SearchBridge()
    
    async def search_all(
        self,
        query: str,
        limit: int = 10
    ) -> List[DatasetCandidate]:
        """
        Search all sources and combine results.
        
        Args:
            query: Search query
            limit: Max results per source
            
        Returns:
            Combined list of candidates
        """
        all_candidates = []
        
        # Source 1: HuggingFace
        logger.info(f"Searching HuggingFace for: {query}")
        try:
            hf_results = await self.hf.search_datasets(query, limit=limit)
            all_candidates.extend(hf_results)
            logger.info(f"  HuggingFace: {len(hf_results)} results")
        except Exception as e:
            logger.warning(f"  HuggingFace search failed: {e}")
        
        # Source 2: Kaggle (if we don't have enough results)
        if len(all_candidates) < limit:
            logger.info(f"Searching Kaggle for: {query}")
            try:
                kaggle_results = await self.kaggle.search_datasets(query, limit=limit)
                all_candidates.extend(kaggle_results)
                logger.info(f"  Kaggle: {len(kaggle_results)} results")
            except Exception as e:
                logger.warning(f"  Kaggle search failed: {e}")
        
        # Source 3: Web scraping (last resort)
        if len(all_candidates) < 3:
            logger.info(f"Searching web for: {query}")
            try:
                web_results = await self.web.fallback_search(query)
                logger.info(f"  Web: {len(web_results)} candidates found")
                
                for r in web_results:
                    from ..schemas import SourceType
                    from pydantic import HttpUrl
                    
                    candidate = DatasetCandidate(
                        source_id=r["title"],
                        source_type=SourceType.WEB_SCRAPE,
                        url=HttpUrl(r["url"]),
                        is_downloadable=False,  # Needs scraping first
                        file_metadata={
                            "size_mb": 0,
                            "file_extension": "unknown",
                            "description": r["snippet"]
                        },
                        compliance_score=0.2  # Low initial score until verified
                    )
                    all_candidates.append(candidate)
                    
            except Exception as e:
                logger.warning(f"  Web search failed: {e}")
        
        logger.info(f"Total results: {len(all_candidates)} from all sources")
        return all_candidates


# Test
async def test_multi_source():
    """Test multi-source search"""
    searcher = MultiSourceSearch()
    
    queries = ["iris", "cancer", "asteroid"]
    
    print("\n" + "="*60)
    print("Multi-Source Search Test")
    print("="*60 + "\n")
    
    for query in queries:
        print(f"Query: '{query}'")
        results = await searcher.search_all(query, limit=5)
        print(f"  Total: {len(results)} results")
        
        for i, r in enumerate(results[:3], 1):
            print(f"    {i}. {r.source_id} ({r.source_type.value})")
        print()


if __name__ == "__main__":
    asyncio.run(test_multi_source())
