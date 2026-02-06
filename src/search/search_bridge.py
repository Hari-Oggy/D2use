import asyncio
from typing import List, Dict
import logging

from .serpapi_client import SerpAPIClient
from .url_classifier import URLClassifier

logger = logging.getLogger(__name__)

class SearchBridge:
    """
    Layer 1.5: Search Engine Bridge
    
    Orchestrates fallback from API search to web search when needed.
    Includes URL filtering to remove junk results.
    """
    
    def __init__(self):
        self.serpapi_client = SerpAPIClient()
        self.url_classifier = URLClassifier()
    
    async def fallback_search(self, query: str, num_results: int = 20) -> List[Dict[str, str]]:
        """
        Perform web search as fallback and return filtered dataset info.
        
        Args:
            query: Search query
            num_results: Number of results to fetch from Google
            
        Returns:
            List of dicts: {"url": str, "title": str, "snippet": str}
        """
        logger.info(f"Executing fallback search for: {query}")
        
        # Step 1: Search Google via SerpAPI
        search_results = await self.serpapi_client.search(query, num_results)
        
        if not search_results:
            logger.warning("No results from web search")
            return []
        
        # Step 2: Extract & Filter
        candidates = []
        for result in search_results:
            url = result.get("link")
            if not url:
                continue
                
            if self.url_classifier.is_dataset_url(url):
                candidates.append({
                    "url": url,
                    "title": result.get("title", "Unknown Dataset"),
                    "snippet": result.get("snippet", "")
                })
        
        logger.info(f"Fallback search complete: {len(candidates)} web candidates found")
        
        return candidates
    
    async def close(self):
        """Close resources"""
        await self.serpapi_client.close()


# Test function
async def test_search_bridge():
    """Test the search bridge"""
    bridge = SearchBridge()
    
    try:
        print(f"\n{'='*60}")
        print("Search Bridge Test: Fallback Search")
        print(f"{'='*60}\n")
        
        urls = await bridge.fallback_search("cancer", num_results=10)
        
        print(f"Found {len(urls)} dataset URLs:\n")
        for i, url in enumerate(urls[:5], 1):
            print(f"{i}. {url}")
        
        print(f"\n{'='*60}\n")
        
    finally:
        await bridge.close()


if __name__ == "__main__":
    asyncio.run(test_search_bridge())
