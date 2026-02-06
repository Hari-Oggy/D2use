import asyncio
from typing import Dict, Optional
import logging

from .simple_scraper import SimpleHTTPScraper

# Try to import Crawlee (optional - requires Playwright)
try:
    from .crawlee_engine import CrawleeEngine
    CRAWLEE_AVAILABLE = True
except ImportError:
    CRAWLEE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Crawlee not available (Playwright not installed). Using simple scraper only.")

logger = logging.getLogger(__name__)

class IntelligentScraper:
    """
    Intelligent scraper that tries simple HTTP first, then falls back to Crawlee.
    
    Strategy:
    1. Try SimpleHTTPScraper (fast, lightweight)
    2. If fails or returns empty content → Fallback to CrawleeEngine (handles JS)
    """
    
    def __init__(self):
        self.simple_scraper = SimpleHTTPScraper()
        self.crawlee_engine = None  # Lazy load (Playwright is heavy)
    
    async def scrape_url(self, url: str) -> Optional[Dict]:
        """
        Intelligently scrape a URL with automatic fallback.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with scraped data or None if both methods fail
        """
        # Try simple scraper first (fast)
        logger.info(f"Attempting simple HTTP scrape: {url}")
        result = await self.simple_scraper.scrape_url(url)
        
        # Check if result is valid
        if result and self._is_valid_result(result):
            logger.info(f"✅ Simple scraper succeeded for {url}")
            return result
        
        # Fallback to Crawlee (handles JavaScript-heavy pages)
        if not CRAWLEE_AVAILABLE:
            logger.warning(f"Crawlee not available, returning simple scraper result for {url}")
            return result  # Return simple scraper result even if empty/failed
        
        logger.warning(f"Simple scraper failed/empty, trying Crawlee for {url}")
        
        try:
            # Lazy load Crawlee engine
            if self.crawlee_engine is None:
                self.crawlee_engine = CrawleeEngine()
            
            result = await self.crawlee_engine.scrape_url(url)
            
            if result and self._is_valid_result(result):
                logger.info(f"✅ Crawlee scraper succeeded for {url}")
                return result
            else:
                logger.error(f"❌ Both scrapers failed for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Crawlee scraper error for {url}: {e}")
            return result  # Return simple scraper result even if empty
    
    def _is_valid_result(self, result: Dict) -> bool:
        """Check if scraping result is valid (has meaningful content)"""
        if not result:
            return False
        
        # Check if HTML content exists and is not empty
        html = result.get("html", "")
        if not html or len(html) < 100:  # Too short = likely error page
            return False
        
        # Check if title exists
        title = result.get("title", "")
        if not title or title.lower() in ["error", "404", "not found"]:
            return False
        
        return True
    
    async def close(self):
        """Close all scrapers"""
        await self.simple_scraper.close()
        if self.crawlee_engine:
            # Crawlee doesn't have close method, but we can clean up if needed
            pass


# ---------------------------------Test function--------------------------------------------
async def test_intelligent_scraper():
    """Test intelligent scraper with real-world URLs"""
    scraper = IntelligentScraper()
    
    # Test URLs (mix of simple and JS-heavy sites)
    test_urls = [
        "https://github.com/datasets/gdp",  # Simple HTML
        "https://zenodo.org/records/3964985",  # May need JS
    ]
    
    print(f"\n{'='*60}")
    print("Intelligent Scraper Test (Real-World URLs)")
    print(f"{'='*60}\n")
    
    for url in test_urls:
        print(f"Testing: {url}")
        result = await scraper.scrape_url(url)
        
        if result:
            print(f"✅ Success!")
            print(f"   Title: {result.get('title', 'N/A')[:50]}...")
            print(f"   HTML length: {len(result.get('html', ''))} chars")
            print(f"   Download links: {len(result.get('download_links', []))}")
        else:
            print(f"❌ Failed")
        print()
    
    await scraper.close()
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(test_intelligent_scraper())
