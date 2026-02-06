import asyncio
import httpx
from typing import List, Dict, Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class SerpAPIClient:
    """
    Client for Google Search API via SerpAPI.
    Provides fallback search when primary APIs (HF, Kaggle) fail or return insufficient results.
    """
    
    BASE_URL = "https://serpapi.com/search"
    
    def __init__(self):
        self.api_key = settings.SERPAPI_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search(self, query: str, num_results: int = 20) -> List[Dict]:
        """
        Search Google for dataset-related results.
        
        Args:
            query: Search query (will be formatted for datasets)
            num_results: Number of results to return
            
        Returns:
            List of search results with 'link', 'title', 'snippet'
        """
        try:
            # Format query to target datasets
            formatted_query = f"{query} dataset filetype:csv OR filetype:json OR filetype:parquet"
            
            logger.info(f"Searching Google via SerpAPI for: {formatted_query}")
            
            params = {
                "q": formatted_query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google"
            }
            
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract organic results
            results = []
            organic_results = data.get("organic_results", [])
            
            for result in organic_results:
                results.append({
                    "link": result.get("link", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "source": "google"
                })
            
            logger.info(f"Found {len(results)} results from Google")
            return results
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("SerpAPI authentication failed. Check SERPAPI_KEY in .env")
            else:
                logger.error(f"SerpAPI HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Test function
async def test_serpapi():
    """Test SerpAPI client"""
    client = SerpAPIClient()
    
    try:
        results = await client.search("cancer", num_results=5)
        
        print(f"\n{'='*60}")
        print(f"SerpAPI Search Results: 'cancer dataset'")
        print(f"{'='*60}\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['link']}")
            print(f"   Snippet: {result['snippet'][:100]}...")
            print()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_serpapi())
